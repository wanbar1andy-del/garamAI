import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Setup paths
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

# Analysis Period: Pre-crash to Recovery
START_DATE = "2025-10-20"
END_DATE = "2025-11-24"

TARGETS = {
    "108490": "Loser #1 (Rank 1)",
    "030530": "Loser #2 (Rank 2)",
    "458870": "Winner (Rank 3)"
}

def calculate_indicators(df):
    # RSI 14
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MA 20 & Divergence
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['dist_ma20'] = (df['close'] - df['ma20']) / df['ma20'] * 100
    
    # Momentum 6m (126 days) - The Ranking Score
    # We simulate the exact metric: (Close / Close_126d_ago) - 1
    df['mom6m'] = df['close'].pct_change(periods=126)
    
    return df

def analyze_forensic():
    print(f"--- Forensic Analysis: {START_DATE} to {END_DATE} ---")
    print(f"{'Date':<12} | {'Symbol':<10} | {'Price':<8} | {'Score(Mom)':<10} | {'RSI':<5} | {'MA20 Dist':<10} | {'Signal?'}")
    print("-" * 90)
    
    full_data = {}
    
    # Load and Prep Data
    for sym, label in TARGETS.items():
        daily_file = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        if not daily_file.exists():
            print(f"Missing data for {sym}")
            continue
            
        df = pd.read_csv(daily_file)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = calculate_indicators(df)
        full_data[sym] = df.loc[START_DATE:END_DATE]

    # Daily Compare
    dates = sorted(list(set([d for sym in full_data for d in full_data[sym].index])))
    
    for d in dates:
        d_str = d.strftime("%Y-%m-%d")
        print(f"\n[ {d_str} ]")
        
        # Collect daily stats to compare ranking
        daily_ranks = []
        for sym in TARGETS:
            if d in full_data[sym].index:
                row = full_data[sym].loc[d]
                daily_ranks.append((sym, row['mom6m'], row['close'], row['rsi'], row['dist_ma20']))
        
        # Sort by Score (Momentum) to see "Simulated Rank"
        daily_ranks.sort(key=lambda x: x[1], reverse=True)
        
        for i, (sym, mom, price, rsi, dist) in enumerate(daily_ranks):
            rank = i + 1
            label = TARGETS[sym]
            
            # Risk/Opp Signals
            signal = ""
            if rsi > 70: signal += "[OVERHEAT] "
            if dist > 30: signal += "[BUBBLE?] "
            if rsi < 30: signal += "[OVERSOLD] "
            if mom > 1.0: signal += "[HIGH_MOM] "
            
            print(f"  Rank #{rank} {sym} ({label}): p={int(price)}, Score={mom*100:.1f}%, RSI={rsi:.0f}, MA20_Dist={dist:.1f}% {signal}")

    print("\n--- Summary ---")
    print("Check points:")
    print("1. Did Losers have 'Bubble' signals (High MA Dist, RSI > 70) before crash?")
    print("2. Did Winner (Rank 3) ever cross Rank 1/2 in Score? (If not, we never would have swapped based on Score alone)")
    print("3. Was there a 'Dead Cross' on Losers?")

analyze_forensic()
