import pandas as pd
import numpy as np
from pathlib import Path

results_dir = Path("g:/내 드라이브/garamdata/experiments/real_sim_champion_v3_final")
equity_file = results_dir / "equity.csv"
trades_file = results_dir / "trades.csv"

def calculate_mdd(equity_curve):
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

print("=== Final Simulation Analysis ===")

if equity_file.exists():
    df_eq = pd.read_csv(equity_file)
    df_eq['date'] = pd.to_datetime(df_eq['date'])
    df_eq.set_index('date', inplace=True)
    
    initial_equity = df_eq['equity'].iloc[0]
    final_equity = df_eq['equity'].iloc[-1]
    total_return = (final_equity - initial_equity) / initial_equity
    mdd = calculate_mdd(df_eq['equity'])
    
    print(f"Initial Equity: {initial_equity:,.0f}")
    print(f"Final Equity:   {final_equity:,.0f}")
    print(f"Total Return:   {total_return*100:.2f}%")
    print(f"Max Drawdown:   {mdd*100:.2f}%")
else:
    print("Equity file not found.")

if trades_file.exists():
    df_trades = pd.read_csv(trades_file)
    if not df_trades.empty:
        total_trades = len(df_trades)
        win_trades = len(df_trades[df_trades['pnl'] > 0])
        win_rate = win_trades / total_trades
        avg_pnl = df_trades['pnl'].mean()
        avg_return = df_trades['return_pct'].mean()
        
        print(f"Total Trades:   {total_trades}")
        print(f"Win Rate:       {win_rate*100:.2f}%")
        print(f"Avg PnL:        {avg_pnl:,.0f}")
        print(f"Avg Return:     {avg_return*100:.2f}%")
        
        # Breakdown by Exit Reason
        print("\nExit Reasons:")
        print(df_trades['exit_reason'].value_counts())
    else:
        print("No trades found.")
else:
    print("Trades file not found.")
