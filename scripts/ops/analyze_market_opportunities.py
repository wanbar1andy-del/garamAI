"""
Market Opportunity Analyzer (>10% Rallies)
Purpose: Count how many times a >10% price increase occurred in the dataset.
Logic:
    - Iterate minute data.
    - Track 'lowest price witnessed so far' (Reference Low).
    - If Price >= Reference Low * 1.10:
        -> EVENT FOUND. Record duration (Time_Now - Time_RefLow).
        -> Reset Reference Low to current price (Start looking for next leg).
    - If Price < Reference Low:
        -> Update Reference Low (Found a better entry price).
    - Constraints: 'Ignore intermediate volatility' is handled by holding until 10% is hit or a lower low resets the entry.
"""
import glob
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm

def analyze_opportunities():
    root_dir = Path("C:/garam/garam/GARAM_Data/60day_replay_kst")
    files = list(root_dir.glob("*.csv"))
    
    results = [] # list of {ticker, start_ts, end_ts, duration_mins, lowest_px, highest_px}
    
    print(f"Analyzing {len(files)} symbols for >10% opportunities...")
    
    for f in tqdm(files):
        try:
            df = pd.read_csv(f)
            # Normalize column names
            col_map = {'ts': 'date', 'date': 'date', 'Date': 'date', 
                       'close': 'close', 'Close': 'close'}
            # Convert map to specific rename dict for columns present
            rename_dict = {k: v for k, v in col_map.items() if k in df.columns}
            df.rename(columns=rename_dict, inplace=True)
            
            if 'date' not in df.columns or 'close' not in df.columns:
                continue
                
            # Ensure float
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df.dropna(subset=['close'], inplace=True)
            
            # Robust Date Conversion
            times = pd.to_datetime(df['date']).tolist() # Convert to list of Timestamps
            prices = df['close'].values
            
            if len(prices) < 2: continue
            
            ref_low = prices[0]
            ref_ts = times[0]
            
            max_gain_seen = 0.0
            
            for i in range(1, len(prices)):
                curr_px = prices[i]
                curr_ts = times[i]
                
                gain = (curr_px / ref_low) - 1.0
                if gain > max_gain_seen: max_gain_seen = gain
                
                # Check Target (10%)
                if curr_px >= ref_low * 1.10:
                    # Found!
                    dur = (curr_ts - ref_ts).total_seconds() / 60.0
                    results.append({
                        'ticker': f.stem,
                        'start_ts': ref_ts,
                        'end_ts': curr_ts,
                        'duration_mins': dur,
                        'start_px': ref_low,
                        'end_px': curr_px
                    })
                    # Reset
                    ref_low = curr_px
                    ref_ts = curr_ts
                    max_gain_seen = 0.0 # Reset stats for new leg
                
                elif curr_px < ref_low:
                    ref_low = curr_px
                    ref_ts = curr_ts
                    
            if len(results) == 0 and len(prices) > 0:
                # Debug sample one symbol
                if f.stem == '005930': # Samsung
                    print(f"DEBUG {f.stem}: Max run gain {max_gain_seen*100:.2f}%")
                    
        except Exception as e:
            print(f"Error processing {f.name}: {e}")
            pass
            
    # Analysis
    if not results:
        print("No opportunities found.")
        return

    df_res = pd.DataFrame(results)
    
    # 1. Unique Stocks
    unique_stocks = df_res['ticker'].nunique()
    total_files = len(files)
    
    # 2. Total Counts
    total_count = len(df_res)
    
    # 3. Time Distribution
    med_time = df_res['duration_mins'].median()
    avg_time = df_res['duration_mins'].mean()
    min_time = df_res['duration_mins'].min()
    
    # 4. Filter by "Quick" vs "Slow" (e.g. < 1 day = 381 mins)
    quick_moves = df_res[df_res['duration_mins'] < 381]
    
    print("\n" + "="*50)
    print("🚀 MARKET OPPORTUNITY ANALYSIS (>10% Rallies)")
    print("="*50)
    print(f"Period: 60 Days (2025-11-07 ~ 2026-01-06)")
    print(f"Total Symbols Analyzed: {total_files}")
    print(f"Symbols with >10% Moves: {unique_stocks} ({unique_stocks/total_files*100:.1f}%)")
    print("-" * 50)
    print(f"Total Occurrences: {total_count}")
    print(f"Avg Occurrences per Symbol: {total_count/total_files:.2f}")
    print(f"Avg Occurrences (Winners Only): {total_count/unique_stocks:.2f}")
    print("-" * 50)
    print("[Time to Hit +10%]")
    print(f"Median Time: {med_time:.0f} mins ({med_time/60:.1f} hours)")
    print(f"Average Time: {avg_time:.0f} mins ({avg_time/60:.1f} hours)")
    print(f"Fastest Time: {min_time:.0f} mins")
    print(f"Intraday (<1 Day) Moves: {len(quick_moves)} ({len(quick_moves)/total_count*100:.1f}%)")
    print("="*50)
    
    # Save Report
    with open("logs/ops/market_opportunities.txt", "w", encoding="utf-8") as f:
        f.write(f"Market Opportunities (>10%)\n")
        f.write(f"Unique Stocks: {unique_stocks}\n")
        f.write(f"Total Count: {total_count}\n")
        f.write(f"Median Time: {med_time:.0f} mins\n")
        f.write(f"Sample Top 5 Fastest:\n")
        f.write(df_res.sort_values('duration_mins').head(5).to_string())

if __name__ == "__main__":
    analyze_opportunities()
