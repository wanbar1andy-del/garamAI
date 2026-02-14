"""
Check Benchmark: Buy & Hold Return vs Simulation Period
Target Period: 2025-10-01 ~ 2026-01-02 (Based on file data)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path("C:/garam/garam")
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"

def main():
    print(f"Scanning data in {DATA_DIR}...")
    files = list(DATA_DIR.glob("*.csv"))
    
    results = []
    
    for f in files:
        if '329180' in f.name: continue # Skip specific exclusion if any
        
        try:
            df = pd.read_csv(f)
            # Normalize column names
            df.rename(columns={'ts':'date', 'Date':'date'}, inplace=True)
            df.sort_values('date', inplace=True)
            
            if df.empty: continue
            
            # Simple Buy & Hold: Buy on Day 1 Open, Sell on Last Day Close
            first_row = df.iloc[0]
            last_row = df.iloc[-1]
            
            start_px = float(first_row['open'])
            end_px = float(last_row['close'])
            
            if start_px <= 0: continue
            
            ret = (end_px - start_px) / start_px
            
            results.append({
                'ticker': f.stem,
                'start_date': first_row['date'],
                'end_date': last_row['date'],
                'return': ret,
                'start_px': start_px,
                'end_px': end_px
            })
            
        except Exception as e:
            # print(f"Error reading {f.name}: {e}")
            pass
            
    if not results:
        print("No valid data found.")
        return

    df_res = pd.DataFrame(results)
    
    # Statistics
    avg_ret = df_res['return'].mean()
    median_ret = df_res['return'].median()
    pos_ratio = (df_res['return'] > 0).mean()
    
    print("-" * 40)
    print(f"Benchmark Analysis (Universe Buy & Hold)")
    print(f"Total Tickers: {len(df_res)}")
    print(f"Avg Return:    {avg_ret*100:.2f}%")
    print(f"Median Return: {median_ret*100:.2f}%")
    print(f"Win Rate (B&H):{pos_ratio*100:.1f}%")
    print("-" * 40)
    
    # Top Gainers (Heroes)
    print("\nTop 20 Heroes (Buy & Hold Return):")
    top20 = df_res.sort_values('return', ascending=False).head(20)
    for i, row in top20.iterrows():
        print(f"{row['ticker']}: {row['return']*100:6.2f}% ({row['start_date']} -> {row['end_date']})")

    # Bottom Losers
    print("\nBottom 5 Losers:")
    bot5 = df_res.sort_values('return', ascending=True).head(5)
    for i, row in bot5.iterrows():
        print(f"{row['ticker']}: {row['return']*100:6.2f}%")

if __name__ == "__main__":
    main()
