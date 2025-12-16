"""
DGE Final Swing Portfolio Backtest (True Hybrid)
- Simulates "Live Runner" logic on historical data.
- Stateful Portfolio (Multi-day Holding).
- Logic:
  - Entry: DGE Intraday (Aggressive Open/Breakout) if Score > 0.15.
  - Exit: Stop Loss (2%) or Trend Break.
  - EOD: If Score > 0.7, HOLD. Else, CLOSE.
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import sys
from datetime import datetime, time, timedelta

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class Position:
    def __init__(self, symbol, entry_price, qty, entry_time, score_at_entry, stop_loss_pct=0.02):
        self.symbol = symbol
        self.entry_price = entry_price
        self.qty = qty
        self.entry_time = entry_time
        self.score_at_entry = score_at_entry
        self.stop_price = entry_price * (1.0 - stop_loss_pct)
        self.is_open = True
        self.exit_price = 0.0
        self.exit_time = None
        self.exit_reason = ""
        self.pnl = 0.0
        
    def update(self, current_price, current_time):
        # Check Stop Loss
        if current_price <= self.stop_price:
            self.close(current_price, current_time, "Stop Loss")
            return True # Closed
        return False # Open

    def close(self, price, time, reason):
        self.is_open = False
        self.exit_price = price
        self.exit_time = time
        self.exit_reason = reason
        self.pnl = (self.exit_price - self.entry_price) * self.qty
        # Fee (0.2%)
        fee = (self.entry_price * self.qty * 0.001) + (self.exit_price * self.qty * 0.001) # Approx
        self.pnl -= fee

def run_swing_backtest(universe_file, scores_file, minute_data_dir, start_date, end_date, initial_capital, min_entry_score, hold_score_thresh, stop_loss_pct, results_dir):
    print("=== DGE Final Swing Portfolio Backtest ===")
    print(f"Stop Loss: {stop_loss_pct*100}%")
    
    # 1. Load Data
    scores_df = pd.read_csv(scores_file)
    scores_df['date'] = pd.to_datetime(scores_df['date'])
    score_matrix = scores_df.pivot(index='date', columns='symbol', values='score').fillna(0)
    
    print("Loading minute data...")
    minute_data = {}
    data_path = Path(minute_data_dir)
    for csv_file in data_path.glob("*_1m.csv"):
        sym = csv_file.stem.split('_')[0]
        df = pd.read_csv(csv_file)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        minute_data[sym] = df
    print(f"Loaded minute data for {len(minute_data)} symbols.")
    
    # 2. Simulation State
    cash = initial_capital
    positions = {} # symbol -> Position
    trades_history = []
    equity_curve = []
    
    dates = score_matrix.index.sort_values()
    dates = [d for d in dates if d >= pd.to_datetime(start_date) and d <= pd.to_datetime(end_date)]
    
    for d in dates:
        date_str = d.strftime("%Y-%m-%d")
        daily_scores = score_matrix.loc[d]
        
        # 1. Update Existing Positions (Intraday Check)
        
        # Identify Candidates for Entry
        candidates = daily_scores[daily_scores >= min_entry_score].sort_values(ascending=False)
        
        # Step A: Check Exits for Existing Positions (Before Market Open / At Open)
        symbols_to_close = []
        for sym, pos in positions.items():
            # Check Score
            current_score = daily_scores.get(sym, 0.0)
            
            # If Score dropped below Hold Threshold, Close at Open
            if current_score < hold_score_thresh: # e.g. 0.7
                # Close at Open
                if str(sym) in minute_data:
                    day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                    if not day_data.empty:
                        exit_price = day_data.iloc[0]['open']
                        pos.close(exit_price, day_data.index[0], f"Score Drop ({current_score:.2f})")
                        cash += (pos.exit_price * pos.qty) - (pos.exit_price * pos.qty * 0.002) # Cash back
                        trades_history.append(pos)
                        symbols_to_close.append(sym)
                    else:
                        # No data, force close at last close?
                        # Assume closed at prev close
                        pos.close(pos.entry_price, d, "No Data (Score Drop)") # Fallback
                        cash += (pos.exit_price * pos.qty)
                        trades_history.append(pos)
                        symbols_to_close.append(sym)
                else:
                    symbols_to_close.append(sym) # Should not happen if data loaded
        
        for sym in symbols_to_close:
            del positions[sym]
            
        # Step B: Intraday Simulation (OHLC) for Held + New
        
        if not positions and cash > (initial_capital * 0.1): # Have cash
            # Pick Top Candidate
            for sym, score in candidates.items():
                if str(sym) not in minute_data: continue
                
                # Enter this symbol
                day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                if day_data.empty: continue
                
                entry_price = day_data.iloc[0]['open']
                qty = int(cash / entry_price)
                if qty > 0:
                    pos = Position(sym, entry_price, qty, day_data.index[0], score, stop_loss_pct)
                    positions[sym] = pos
                    cash -= (entry_price * qty)
                    # Fee
                    cash -= (entry_price * qty * 0.001)
                    break # Only 1 position
        
        # Step C: Simulate Intraday Price Action (Stop Loss)
        # For all open positions, check Low vs Stop Loss
        symbols_stopped_out = []
        
        for sym, pos in positions.items():
            if str(sym) not in minute_data: continue
            day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
            if day_data.empty: continue
            
            low_price = day_data['low'].min()
            
            if pos.update(low_price, day_data.index[-1]): # Checks Stop Loss
                # Closed by Stop Loss
                cash += (pos.exit_price * pos.qty)
                trades_history.append(pos)
                symbols_stopped_out.append(sym)
                
        for sym in symbols_stopped_out:
            del positions[sym]
            
        # Step D: EOD Decision (Hold vs Exit)
        
        symbols_eod_close = []
        for sym, pos in positions.items():
            current_score = daily_scores.get(sym, 0.0)
            
            # If we used hold_score_thresh for Open Exit, we shouldn't check it again here for EOD Exit?
            # Actually, we check it at Open to see if we should have held.
            # If we survived Open, we hold until EOD.
            # At EOD, we check if we should hold for TOMORROW.
            # But we only have TODAY's score (calculated at EOD).
            # So yes, we check again.
            # If Score <= Threshold, we Close at Close.
            
            if current_score < hold_score_thresh:
                # Close at Close
                if str(sym) in minute_data:
                    day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                    if not day_data.empty:
                        exit_price = day_data.iloc[-1]['close']
                        pos.close(exit_price, day_data.index[-1], f"EOD Score Low ({current_score:.2f})")
                        cash += (pos.exit_price * pos.qty)
                        trades_history.append(pos)
                        symbols_eod_close.append(sym)
        
        for sym in symbols_eod_close:
            del positions[sym]
            
        # Calculate Equity
        equity = cash
        exposure = 0
        for sym, pos in positions.items():
            # Mark to Market (Close Price)
            if str(sym) in minute_data:
                day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                if not day_data.empty:
                    current_price = day_data.iloc[-1]['close']
                    equity += (current_price * pos.qty)
                    exposure += 1
            else:
                equity += (pos.entry_price * pos.qty) # Stale price
                
        equity_curve.append({
            'date': d,
            'equity': equity,
            'cash': cash,
            'positions': len(positions)
        })
        
    # Force Close Remaining Positions
    for sym, pos in positions.items():
        # Close at last known price
        if str(sym) in minute_data:
            day_data = minute_data[str(sym)]
            if not day_data.empty:
                exit_price = day_data.iloc[-1]['close']
                pos.close(exit_price, day_data.index[-1], "End of Simulation")
                trades_history.append(pos)
    
    # Save Results
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    pd.DataFrame(equity_curve).set_index('date').to_csv(Path(results_dir) / "equity_curve.csv")
    
    # Save Trades
    trades_data = []
    for t in trades_history:
        trades_data.append({
            'symbol': t.symbol,
            'entry_time': t.entry_time,
            'exit_time': t.exit_time,
            'entry_price': t.entry_price,
            'exit_price': t.exit_price,
            'qty': t.qty,
            'pnl': t.pnl,
            'return_pct': (t.exit_price - t.entry_price) / t.entry_price,
            'exit_reason': t.exit_reason
        })
    pd.DataFrame(trades_data).to_csv(Path(results_dir) / "trades.csv", index=False)
    
    final_equity = equity_curve[-1]['equity']
    total_return = (final_equity - initial_capital) / initial_capital
    print("-" * 30)
    print(f"Final Equity: {final_equity:,.0f}")
    print(f"Total Return: {total_return*100:.2f}%")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--universe-file', required=True)
    parser.add_argument('--scores-file', required=True)
    parser.add_argument('--minute-data-dir', required=True)
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    parser.add_argument('--initial-capital', type=float, required=True)
    parser.add_argument('--min-entry-score', type=float, default=0.15)
    parser.add_argument('--hold-score-thresh', type=float, default=0.7)
    parser.add_argument('--stop-loss-pct', type=float, default=0.02)
    parser.add_argument('--results-dir', required=True)
    args = parser.parse_args()
    
    run_swing_backtest(
        args.universe_file,
        args.scores_file,
        args.minute_data_dir,
        args.start_date,
        args.end_date,
        args.initial_capital,
        args.min_entry_score,
        args.hold_score_thresh,
        args.stop_loss_pct,
        args.results_dir
    )

if __name__ == "__main__":
    main()
