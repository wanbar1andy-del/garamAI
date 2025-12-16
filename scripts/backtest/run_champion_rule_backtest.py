import sys
from pathlib import Path
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, time, timedelta

# Add project root
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent # c:\garam\garam
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import yaml
from micro_regime import calculate_latest_micro_regime

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

def load_profile(profile_path):
    with open(profile_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def is_entry_allowed(regime, micro, profile):
    rp = profile["regime_policy"].get(regime)
    if not rp:
        return False # Default Block if undefined
        
    # Check Mode
    if rp.get("mode") == "CASH_ONLY":
        return False
        
    # Check Guardrails
    guard = rp.get("guardrail", {})
    if guard.get("trading_enabled") is False:
        return False
        
    banned_micros = guard.get("micro_ban", [])
    if micro in banned_micros:
        return False
        
    return True

def run_champion_backtest(universe_file, scores_file, minute_data_dir, start_date, end_date, initial_capital, profile_path, results_dir):
    # Load Profile
    profile = load_profile(profile_path)
    t_gate = profile['core']['gate']
    max_positions = profile['core']['max_positions']
    stop_loss_pct = 0.08 # Default hardcoded for now or add to profile
    
    print(f"=== Champion Rule Backtest (Profile: {profile['profile_name']}) ===")
    print(f"Gate: {t_gate}, MaxPos: {max_positions}")
    
    # 1. Load Data
    scores_df = pd.read_csv(scores_file, dtype={'symbol': str})
    scores_df['symbol'] = scores_df['symbol'].str.zfill(6)
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
    
    # Load Market Proxy for Regime (005930)
    proxy_sym = "005930"
    if proxy_sym in minute_data:
        market_df = minute_data[proxy_sym].resample('D').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
    else:
        print("WARNING: Market Proxy (005930) not found in minute data. Regime checks will fail.")
        market_df = pd.DataFrame()

    # Universe Size Check
    if len(minute_data) < 30:
        raise ValueError(f"INVALID UNIVERSE: Only {len(minute_data)} symbols loaded. Minimum 30 required for Champion Rule.")
    
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
        
        # --- Determine Market Regime & Micro Regime (Morning) ---
        # We use data UP TO Yesterday (d - 1 day)
        # Find index of d in market_df
        current_regime = "R7_UNKNOWN"
        current_micro = "MR_UNKNOWN"
        
        if not market_df.empty:
            # Get data up to yesterday
            history = market_df[market_df.index < d]
            if not history.empty:
                # Calculate Main Regime (Simplified)
                last_row = history.iloc[-1]
                ma20 = history['close'].rolling(20).mean().iloc[-1]
                ma60 = history['close'].rolling(60).mean().iloc[-1]
                mom = last_row['close'] / history['close'].shift(20).iloc[-1]
                
                if last_row['close'] > ma20:
                    if mom > 1.05:
                        current_regime = "R1_STRONG_UP"
                    else:
                        current_regime = "R2_GRIND_UP"
                else:
                    if last_row['close'] > ma60:
                        current_regime = "R3_CHOP"
                    else:
                        current_regime = "R4_DOWN"
                        
                # Calculate Micro Regime
                current_micro = calculate_latest_micro_regime(history)
        
        # Check Global Entry Permission
        entry_allowed = is_entry_allowed(current_regime, current_micro, profile)
        
        # --- Layer 2: Portfolio Allocation (Morning) ---
        
        # 1. Calculate Current Equity (Cash + Market Value of Held Positions)
        current_equity = cash
        for sym, pos in positions.items():
            # Mark to Market (Open Price)
            if str(sym) in minute_data:
                day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                if not day_data.empty:
                    current_equity += (day_data.iloc[0]['open'] * pos.qty)
                else:
                    current_equity += (pos.entry_price * pos.qty)
            else:
                current_equity += (pos.entry_price * pos.qty)
                
        # 2. Determine Target Allocation
        target_weights = {}
        
        if entry_allowed:
            # Filter Candidates to those with Data (Backtest Limitation)
            available_symbols = set(minute_data.keys())
            candidates = daily_scores[daily_scores.index.isin(available_symbols)].sort_values(ascending=False)
            
            remaining_weight = 1.0
            allocated_count = 0
            
            for sym, score in candidates.items():
                if score < t_gate: continue
                if remaining_weight <= 0: break
                if allocated_count >= max_positions: break # Max Positions Limit
                
                weight = min(score, remaining_weight)
                target_weights[sym] = weight
                remaining_weight -= weight
                allocated_count += 1
        else:
            # Cash Only Mode
            pass # target_weights remains empty -> Sell All
            
        # 3. Rebalance (Sell first, then Buy)
        
        # SELL Logic
        symbols_to_close = []
        for sym, pos in positions.items():
            target_w = target_weights.get(sym, 0.0)
            
            # If we need to reduce significantly or close
            if target_w == 0:
                # Close
                if str(sym) in minute_data:
                    day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                    if not day_data.empty:
                        exit_price = day_data.iloc[0]['open']
                        pos.close(exit_price, day_data.index[0], "Allocation 0")
                        cash += (pos.exit_price * pos.qty) - (pos.exit_price * pos.qty * 0.002)
                        trades_history.append(pos)
                        symbols_to_close.append(sym)
                    else:
                         # No data
                        symbols_to_close.append(sym)
                else:
                    symbols_to_close.append(sym)
            
        for sym in symbols_to_close:
            del positions[sym]
            
        # BUY Logic
        for sym, target_w in target_weights.items():
            if sym in positions: continue # Already held
            
            # New Entry
            target_amt = target_w * current_equity
            if cash < target_amt * 0.9: # Not enough cash (maybe held in other positions)
                target_amt = cash # Buy with what we have
                
            if target_amt < (current_equity * 0.05): continue # Too small
            
            if str(sym) in minute_data:
                day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                if not day_data.empty:
                    entry_price = day_data.iloc[0]['open']
                    qty = int(target_amt / entry_price)
                    if qty > 0:
                        pos = Position(sym, entry_price, qty, day_data.index[0], daily_scores.get(sym, 0), stop_loss_pct)
                        positions[sym] = pos
                        cash -= (entry_price * qty)
                        cash -= (entry_price * qty * 0.001) # Fee
                        
        # --- Layer 3: Intraday & EOD ---
        
        # Intraday Stop Loss
        symbols_stopped_out = []
        for sym, pos in positions.items():
            if str(sym) not in minute_data: continue
            day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
            if day_data.empty: continue
            
            low_price = day_data['low'].min()
            if pos.update(low_price, day_data.index[-1]):
                cash += (pos.exit_price * pos.qty)
                trades_history.append(pos)
                symbols_stopped_out.append(sym)
                
        for sym in symbols_stopped_out:
            del positions[sym]
            
        # EOD Smart Swing Decision
        symbols_eod_close = []
        for sym, pos in positions.items():
            # Check Layer 3 Conditions
            # 1. Score >= 0.5 (Implies Regime is Good)
            # 2. PnL > 0
            
            current_score = daily_scores.get(sym, 0.0)
            
            # Get Close Price
            if str(sym) in minute_data:
                day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                if not day_data.empty:
                    close_price = day_data.iloc[-1]['close']
                    pnl_pct = (close_price - pos.entry_price) / pos.entry_price
                    
                    # Smart Swing Logic (v2)
                    # Score >= 0.5 AND PnL >= 0
                    
                    if current_score >= 0.5:
                        should_hold = (pnl_pct >= 0.0)
                    else:
                        should_hold = False
                    
                    if not should_hold:
                        # Close
                        pos.close(close_price, day_data.index[-1], f"Smart Swing Exit (S:{current_score:.2f}, P:{pnl_pct*100:.1f}%)")
                        cash += (pos.exit_price * pos.qty)
                        trades_history.append(pos)
                        symbols_eod_close.append(sym)
                        
        for sym in symbols_eod_close:
            del positions[sym]
            
        # Calculate Daily Equity
        equity = cash
        for sym, pos in positions.items():
            if str(sym) in minute_data:
                day_data = minute_data[str(sym)][minute_data[str(sym)].index.date == d.date()]
                if not day_data.empty:
                    equity += (day_data.iloc[-1]['close'] * pos.qty)
                else:
                    equity += (pos.entry_price * pos.qty)
            else:
                equity += (pos.entry_price * pos.qty)
                
        equity_curve.append({
            'date': d,
            'equity': equity,
            'cash': cash,
            'positions': len(positions)
        })

    # Final Close
    for sym, pos in positions.items():
        if str(sym) in minute_data:
            day_data = minute_data[str(sym)]
            if not day_data.empty:
                pos.close(day_data.iloc[-1]['close'], day_data.index[-1], "End of Sim")
                trades_history.append(pos)

    # Save
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    pd.DataFrame(equity_curve).set_index('date').to_csv(Path(results_dir) / "equity_curve.csv")
    
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
    
    # MDD Calculation
    equity_series = pd.DataFrame(equity_curve)['equity']
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak
    max_drawdown = drawdown.min()
    
    # CAGR Calculation (Approx 6 months)
    days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
    cagr = ((final_equity / initial_capital) ** (365/days)) - 1
    
    print("-" * 30)
    print(f"Final Equity: {final_equity:,.0f}")
    print(f"Total Return: {total_return*100:.2f}%")
    print(f"CAGR: {cagr*100:.2f}%")
    print(f"Max Drawdown: {max_drawdown*100:.2f}%")
    
    # Success Criteria Check
    success = (cagr >= 0.30) and (max_drawdown >= -0.60)
    status = "SUCCESS" if success else "FAIL"
    print(f"RESULT: status={status}, CAGR={cagr*100:.1f}%, Return={total_return*100:.1f}%, MDD={max_drawdown*100:.1f}%")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--universe-file', required=True)
    parser.add_argument('--scores-file', required=True)
    parser.add_argument('--minute-data-dir', required=True)
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    parser.add_argument('--initial-capital', type=float, required=True)
    parser.add_argument('--profile', required=True) # New Arg
    parser.add_argument('--results-dir', required=True)
    args = parser.parse_args()
    
    run_champion_backtest(
        args.universe_file,
        args.scores_file,
        args.minute_data_dir,
        args.start_date,
        args.end_date,
        args.initial_capital,
        args.profile,
        args.results_dir
    )

if __name__ == "__main__":
    main()
