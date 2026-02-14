"""
Forensic Analysis: Why did we miss the Heroes?
Target: 000660 (SK Hynix) - Missed
Target: 030530 (Hero) - Mishandled
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path("C:/garam/garam")
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"

# X-7 Config Re-construction
MIN_ENTRY_SCORE = 8.0
MIN_DAILY_VOLATILITY = 0.015 # 1.5%

def analyze_ticker(ticker):
    print(f"\n[Forensics] Analyzing {ticker}...")
    files = list(DATA_DIR.glob(f"*{ticker}*.csv"))
    if not files:
        print("  File not found.")
        return

    f = files[0]
    df = pd.read_csv(f)
    df.rename(columns={'ts':'date', 'Date':'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    
    # Daily aggregation
    df['day'] = df['date'].dt.date
    daily = df.groupby('day').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index()
    
    # Calculate Metrics
    daily['range_pct'] = (daily['high'] - daily['low']) / daily['open']
    daily['turnover'] = daily['close'] * daily['volume']
    
    # Simulated Entry Score (Simplified)
    # Score ~= Ret5 * VolSpike * 100
    # We can't perfectly reproduce minute-level score here without re-running engine,
    # but we can check if it passed the "Macro Filters" (Volatility).
    
    print(f"  {'Date':<12} | {'Close':<8} | {'Range%':<8} | {'VolPass?':<8} | {'Comment'}")
    print("-" * 60)
    
    avg_range_5d = []
    
    for i, row in daily.iterrows():
        r = row['range_pct']
        avg_range_5d.append(r)
        if len(avg_range_5d) > 5: avg_range_5d.pop(0)
        
        avg_r = sum(avg_range_5d)/len(avg_range_5d)
        vol_pass = avg_r >= MIN_DAILY_VOLATILITY
        
        comment = ""
        if not vol_pass: comment = f"Low Vol (Avg {avg_r*100:.2f}%)"
        elif r > 0.05: comment = "Big Day!"
        
        print(f"  {str(row['day']):<12} | {row['close']:<8.0f} | {r*100:6.2f}% | {str(vol_pass):<8} | {comment}")

def main():
    analyze_ticker("000660") # SK Hynix
    analyze_ticker("030530") # Hero

if __name__ == "__main__":
    main()
