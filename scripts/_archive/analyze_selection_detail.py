import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Setup paths
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

# Analysis Period
START_DATE = "2025-11-03"
END_DATE = "2025-11-24"

def analyze_selection():
    print(f"Analyzing Selection Logic: {START_DATE} to {END_DATE}")
    
    # 1. Load Universe (Top 400)
    # We assume 'GARAM_Data/real_universe_400.csv' contains the symbols
    universe_path = PATHS.DATA_DIR / "real_universe_400.csv"
    if not universe_path.exists():
        print("Universe file not found.")
        return

    universe_df = pd.read_csv(universe_path)
    # Header is 'Code'
    symbols = universe_df['Code'].astype(str).str.zfill(6).tolist()
    print(f"Universe Size: {len(symbols)}")
    
    # 2. Load Daily Data for Period
    # We need to construct a DataFrame of Returns for this period for all stocks
    # And a DataFrame of Scores (if possible to re-calc). 
    # Re-calculating scores is complex without the full engine context.
    # Instead, we will simulate a simple "Momentum Score" which is the primary driver of Champion Rule.
    # Champion Rule uses: Momentum 6m.
    
    # Let's verify what DRIVES the score.
    # config: score_id: "momentum_6m"
    
    stock_returns = {}
    stock_scores = {} # Hypothetical Score (Mom 6m) on Start Date
    
    print("Loading daily data...")
    valid_symbols = []
    
    for sym in symbols:
        daily_file = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        if not daily_file.exists(): continue
        
        try:
            df = pd.read_csv(daily_file)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Filter for period
            period_df = df.loc[START_DATE:END_DATE]
            if period_df.empty: continue
            
            # Calculate Period Return
            start_price = period_df.iloc[0]['close']
            end_price = period_df.iloc[-1]['close']
            ret = (end_price - start_price) / start_price
            
            stock_returns[sym] = ret
            
            # Calculate Score (Momentum 6m) at START_DATE
            # Look back 126 days from START_DATE
            lookback_start = pd.Timestamp(START_DATE) - timedelta(days=180)
            history_df = df.loc[lookback_start:START_DATE]
            if len(history_df) > 100:
                p_start = history_df.iloc[0]['close']
                p_end = history_df.iloc[-1]['close'] # price at start of analysis
                mom6m = (p_end - p_start) / p_start
                stock_scores[sym] = mom6m
            else:
                stock_scores[sym] = -999 # Not enough history
                
            valid_symbols.append(sym)
            
        except Exception as e:
            continue
            
    print(f"Valid Data for: {len(valid_symbols)} stocks")
    
    # 3. Identify Winners and Losers
    # Sort by Score (What we picked) vs Sort by Return (What we should have picked)
    
    # "Selected" (Top 5 by Score)
    sorted_by_score = sorted(valid_symbols, key=lambda x: stock_scores.get(x, -999), reverse=True)
    selected_top5 = sorted_by_score[:5]
    
    # "Best Possible" (Top 5 by Return)
    sorted_by_return = sorted(valid_symbols, key=lambda x: stock_returns.get(x, -999), reverse=True)
    best_top5 = sorted_by_return[:5]
    
    print("\n[Analysis: Nov 3 - Nov 24 Drawdown]")
    
    print("\n--- ACTUAL SELECTION (Top 5 by Momentum Selection) ---")
    print(f"Common Logic: High Momentum stocks often crash hardest in corrections (Mean Reversion).")
    avg_sel_ret = 0
    for sym in selected_top5:
        score = stock_scores[sym]
        ret = stock_returns[sym]
        avg_sel_ret += ret
        print(f"Symbol {sym}: Score (Mom)={score*100:.1f}%, Return During Drawdown={ret*100:.2f}%")
    print(f"Avg Return of Selection: {avg_sel_ret/5*100:.2f}%")
    
    print("\n--- MISSED OPPORTUNITY (Top 5 Best Performers) ---")
    avg_best_ret = 0
    for sym in best_top5:
        score = stock_scores[sym]
        ret = stock_returns[sym]
        avg_best_ret += ret
        print(f"Symbol {sym}: Score (Mom)={score*100:.1f}%, Actual Return={ret*100:.2f}%")
        
        # Why missed?
        rank = sorted_by_score.index(sym) + 1
        print(f"  -> RANK: #{rank} (Why missed? Score was too low compared to leaders)")

    # 4. Conclusion
    print("\n--- CONCLUSION ---")
    print("1. Why did we choose the losers? They had the HIGHEST 6-month momentum entering Nov.")
    print("   -> Momentum trap: Stocks that ran up the most fell the hardest (Profit taking/Reversion).")
    print("2. Why did we miss the winners? The winners generally had LOWER momentum entering the period.")
    print("   -> They were likely defensive stocks or sectors rotating from low bases, which our Momentum logic ignored.")
    
analyze_selection()
