import pandas as pd
import numpy as np
from pathlib import Path

def main():
    results_dir = Path("g:/내 드라이브/garamdata/experiments/real_sim_champion_v3_final")
    trades_path = results_dir / "trades.csv"
    equity_path = results_dir / "equity.csv"
    
    if not trades_path.exists() or not equity_path.exists():
        print("Error: Results files not found.")
        return

    # 1. Load Data
    df_trades = pd.read_csv(trades_path)
    df_equity = pd.read_csv(equity_path)
    
    df_trades['entry_time'] = pd.to_datetime(df_trades['entry_time'])
    df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])
    df_equity['date'] = pd.to_datetime(df_equity['date'])
    df_equity.set_index('date', inplace=True)

    # 2. Identify Max Drawdown Period
    running_max = df_equity['equity'].cummax()
    drawdown = (df_equity['equity'] - running_max) / running_max
    
    mdd_val = drawdown.min()
    mdd_date = drawdown.idxmin()
    
    # Find the peak before the MDD
    # We look for the last time drawdown was 0 before mdd_date
    peak_date = drawdown[drawdown == 0].loc[:mdd_date].index[-1]
    
    print(f"MDD Period: {peak_date.date()} ~ {mdd_date.date()} ({mdd_val*100:.2f}%)")
    
    # 3. Filter Trades during MDD Period
    # Trade entry must be within the period
    mask_period = (df_trades['entry_time'] >= peak_date) & (df_trades['entry_time'] <= mdd_date)
    df_period = df_trades[mask_period].copy()
    
    # 4. Analyze Losing Trades
    losing_trades = df_period[df_period['pnl'] < 0].copy()
    
    if losing_trades.empty:
        print("No losing trades found in MDD period (Unlikely).")
        return
        
    # Calculate Duration in Minutes
    # Assuming market hours 9:00 - 15:30 (390 mins)
    # Simple timedelta might include overnight if held multi-day.
    # But A7/A8 are daily rebalance? Or intraday?
    # A4 is intraday. A5/A6/A8 are daily.
    # If daily, duration is usually 1 day (hold overnight).
    # Let's check the actual timestamps.
    
    losing_trades['duration'] = losing_trades['exit_time'] - losing_trades['entry_time']
    losing_trades['duration_mins'] = losing_trades['duration'].dt.total_seconds() / 60
    
    avg_duration = losing_trades['duration_mins'].mean()
    median_duration = losing_trades['duration_mins'].median()
    max_duration = losing_trades['duration_mins'].max()
    min_duration = losing_trades['duration_mins'].min()
    
    print(f"\n[Losing Trades Analysis during MDD]")
    print(f"Count: {len(losing_trades)} trades")
    print(f"Average Duration: {avg_duration:.1f} minutes")
    print(f"Median Duration:  {median_duration:.1f} minutes")
    print(f"Min Duration:     {min_duration:.1f} minutes")
    print(f"Max Duration:     {max_duration:.1f} minutes")
    
    # Check if they are mostly overnight (approx 1440 mins or more) or intraday
    overnight_cnt = (losing_trades['duration_mins'] > 390).sum()
    intraday_cnt = len(losing_trades) - overnight_cnt
    print(f"Overnight Trades: {overnight_cnt} ({overnight_cnt/len(losing_trades)*100:.1f}%)")
    print(f"Intraday Trades:  {intraday_cnt} ({intraday_cnt/len(losing_trades)*100:.1f}%)")

if __name__ == "__main__":
    main()
