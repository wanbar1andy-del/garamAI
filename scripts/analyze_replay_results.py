"""
Analyze Replay Results
- Calculate 1-Day Forward Return for all orders
- Generate Equity Curve
- Metrics: Win Rate, Avg Return, Total Return
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from scripts.load_minute_robust import MinuteDataLoader

def analyze_results(run_dir: str):
    run_path = Path(run_dir)
    orders_path = run_path / "all_orders.csv"
    
    if not orders_path.exists():
        print("No all_orders.csv found")
        return

    df_orders = pd.read_csv(orders_path)
    df_orders["date"] = df_orders["date"].astype(str)
    
    print(f"Loaded {len(df_orders)} orders from {run_dir}")
    
    # Group by symbol to optimize data loading
    orders_by_symbol = df_orders.groupby("symbol")
    
    loader = MinuteDataLoader(Path("GARAM_Data/history/minute"))
    
    results = []
    
    # Iterate symbols
    for symbol, group in orders_by_symbol:
        # Load data
        df_price, _ = loader.load_symbol(str(symbol).zfill(6), lookback_days=400, tail_rows=50000)
        
        if df_price.empty:
            continue
            
        df_price["date"] = df_price["dt"].dt.strftime("%Y%m%d")
        # Set date as index for fast lookup
        # Problem: minute data has multiple rows per date. We need "Close" of the day.
        # Group by date and take last
        df_daily = df_price.groupby("date")["close"].last()
        
        # Get list of trading days (dates)
        trading_dates = sorted(df_daily.index.tolist())
        date_map = {d: i for i, d in enumerate(trading_dates)}
        
        for idx, row in group.iterrows():
            entry_date = str(row["date"])
            entry_price = row["price"]
            
            if entry_date not in date_map:
                continue
                
            entry_idx = date_map[entry_date]
            
            # Find next day
            if entry_idx + 1 >= len(trading_dates):
                # No next day data (last day of simulation?)
                exit_price = entry_price # Flat
                exit_date = "HOLD"
            else:
                exit_date = trading_dates[entry_idx + 1]
                exit_price = df_daily.loc[exit_date]
            
            ret = (exit_price - entry_price) / entry_price
            # Cost: 0.3% (30bps)
            net_ret = ret - 0.003
            
            results.append({
                "date": entry_date,
                "exit_date": exit_date,
                "symbol": symbol,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "raw_ret": ret,
                "net_ret": net_ret
            })
            
    df_res = pd.DataFrame(results)
    df_res.to_csv(run_path / "trade_results.csv", index=False)
    
    # Stats
    win_rate = (df_res["net_ret"] > 0).mean() * 100
    avg_ret = df_res["net_ret"].mean() * 100
    total_trades = len(df_res)
    
    print("\n=== PERFORMANCE SUMMARY (1-Day Hold) ===")
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Avg Return: {avg_ret:.2f}%")
    
    # Equity Curve
    # Assume equal weight per trade (simple sum of returns to see alpha quality)
    # Group by entry date
    daily_rets = df_res.groupby("date")["net_ret"].mean()
    daily_rets.index = pd.to_datetime(daily_rets.index)
    daily_rets = daily_rets.sort_index()
    
    equity = (1 + daily_rets).cumprod()
    
    print(f"Total Cumulative Return: {(equity.iloc[-1] - 1)*100:.2f}%")
    
    # Save Equity CSV for Verification
    df_equity = pd.DataFrame({"net_ret": daily_rets.values, "equity": equity.values}, index=daily_rets.index)
    df_equity.index.name = "date"
    equity_csv_path = run_path / "equity_curve.csv"
    df_equity.to_csv(equity_csv_path)
    print(f"Saved equity CSV: {equity_csv_path}")

    # Plot
    plt.figure(figsize=(12, 6))
    equity.plot(title=f"1-Month Replay Equity (1-Day Hold)\nWinRate: {win_rate:.1f}% | AvgRet: {avg_ret:.2f}%", grid=True)
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return (Base 1.0)")
    out_img = run_path / "equity_curve.png"
    plt.savefig(out_img)
    print(f"Saved plot: {out_img}")
    
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_dir", help="Specific run directory to analyze")
    args = parser.parse_args()
    
    if args.run_dir:
        target_run = Path(args.run_dir)
        if not target_run.exists():
            print(f"Run directory not found: {target_run}")
            sys.exit(1)
        analyze_results(target_run)
        sys.exit(0)

    # Find latest run with all_orders.csv
    root = Path("results/replay")
    runs = sorted([d for d in root.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
    
    target_run = None
    for r in runs:
        if (r / "all_orders.csv").exists():
            target_run = r
            break
            
    if target_run:
        analyze_results(target_run)
    else:
        print("No completed replay runs found (missing all_orders.csv)")
