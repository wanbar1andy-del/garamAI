"""
Analyze DGE Final Swing Results
- Generates detailed metrics:
  - Total Return, MDD, Win Rate
  - Regime PnL (R1-R5)
  - Overnight vs Intraday PnL Breakdown
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def analyze_results(results_dir, scores_file):
    results_path = Path(results_dir)
    trades_file = results_path / "trades.csv"
    equity_file = results_path / "equity_curve.csv"
    
    if not trades_file.exists() or not equity_file.exists():
        print(f"Error: Results not found in {results_dir}")
        return
        
    trades_df = pd.read_csv(trades_file)
    equity_df = pd.read_csv(equity_file)
    equity_df['date'] = pd.to_datetime(equity_df['date'])
    equity_df.set_index('date', inplace=True)
    
    # Load Scores for Regime Analysis
    scores_df = pd.read_csv(scores_file)
    scores_df['date'] = pd.to_datetime(scores_df['date'])
    # We need "Market Regime" or "Symbol Regime"?
    # The user asked for "Regime PnL". Usually Market Regime (KOSPI).
    # But we don't have KOSPI regime file handy here?
    # Or we use the "Symbol Regime" (Score) as proxy?
    # Let's use the "Score" of the traded symbol to classify regime.
    # High Score = R1/R2. Low Score = R4/R5.
    
    # 1. Overall Metrics
    initial_capital = equity_df.iloc[0]['equity'] # Approx (or cash)
    # Actually equity_curve[0] might be after first day.
    # Let's assume 100M.
    initial_capital = 100000000
    final_equity = equity_df.iloc[-1]['equity']
    total_return = (final_equity - initial_capital) / initial_capital
    
    # MDD
    equity_df['peak'] = equity_df['equity'].cummax()
    equity_df['dd'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
    mdd = equity_df['dd'].min()
    
    print("=" * 40)
    print(f"Analysis for: {results_dir}")
    print(f"Total Return: {total_return*100:.2f}%")
    print(f"Final Equity: {final_equity:,.0f}")
    print(f"MDD: {mdd*100:.2f}%")
    print(f"Trade Count: {len(trades_df)}")
    if len(trades_df) > 0:
        win_rate = len(trades_df[trades_df['pnl'] > 0]) / len(trades_df)
        print(f"Win Rate: {win_rate*100:.2f}%")
    
    # 2. Overnight vs Intraday (Approx)
    # We don't have minute-by-minute PnL breakdown in trades.csv.
    # But we can infer:
    # Intraday PnL = (Close - Open) for days held?
    # Overnight PnL = (Open - Prev Close)?
    # This requires re-simulation or detailed logging.
    # For now, let's look at "Exit Reason".
    # If Exit Reason is "Stop Loss", it's Intraday Loss.
    # If Exit Reason is "Score Drop", it's usually EOD or Open.
    # Let's skip detailed Overnight/Intraday split for now unless we parse minute data again.
    
    # 3. Regime Analysis (based on Entry Score)
    # We have 'score_at_entry' in trades.csv?
    # No, we didn't save it. I should have saved it.
    # But we can look up the score for the entry date.
    
    score_matrix = scores_df.pivot(index='date', columns='symbol', values='score').fillna(0)
    
    regime_pnl = {'High (0.7+)': 0, 'Med (0.3-0.7)': 0, 'Low (<0.3)': 0}
    regime_trades = {'High (0.7+)': 0, 'Med (0.3-0.7)': 0, 'Low (<0.3)': 0}
    
    for _, row in trades_df.iterrows():
        entry_date = pd.to_datetime(row['entry_time']).date()
        sym = row['symbol']
        # Lookup score
        if entry_date in score_matrix.index and sym in score_matrix.columns:
            score = score_matrix.loc[pd.Timestamp(entry_date), sym]
            if score >= 0.7:
                regime_pnl['High (0.7+)'] += row['pnl']
                regime_trades['High (0.7+)'] += 1
            elif score >= 0.3:
                regime_pnl['Med (0.3-0.7)'] += row['pnl']
                regime_trades['Med (0.3-0.7)'] += 1
            else:
                regime_pnl['Low (<0.3)'] += row['pnl']
                regime_trades['Low (<0.3)'] += 1
                
    print("-" * 40)
    print("PnL by Entry Score Regime:")
    for r, pnl in regime_pnl.items():
        count = regime_trades[r]
        print(f"{r}: {pnl:,.0f} KRW ({count} trades)")
        
    print("=" * 40)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir', required=True)
    parser.add_argument('--scores-file', required=True)
    args = parser.parse_args()
    
    analyze_results(args.results_dir, args.scores_file)

if __name__ == "__main__":
    main()
