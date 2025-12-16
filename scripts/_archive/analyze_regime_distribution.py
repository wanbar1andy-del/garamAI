import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from regime.micro_regime import calculate_latest_micro_regime, classify_micro_regime

def main():
    # Load 1-year daily data for a representative symbol (e.g., 005930 Samsung Electronics)
    # Or load KOSPI index if available.
    # Let's use 005930 as proxy.
    symbol = "005930"
    data_dir = Path("g:/내 드라이브/garamdata/history")
    # Try multiple possible filenames
    possible_files = [
        data_dir / "KR_005930_SamsungElec_daily_20y.csv",
        data_dir / "daily" / "005930.csv",
        data_dir / "daily" / "KR_005930_SamsungElec_daily_20y.csv"
    ]
    
    file_path = None
    for p in possible_files:
        if p.exists():
            file_path = p
            break
            
    if not file_path:
        print(f"File not found in: {data_dir}")
        return
        
    df = pd.read_csv(file_path)
    # Check column names
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    else:
        print(f"Unknown date column: {df.columns}")
        return
        
    df.sort_index(inplace=True)
    
    # Filter for 2024-12 ~ 2025-12
    start_date = pd.to_datetime("2024-12-01")
    end_date = pd.to_datetime("2025-12-01")
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    print(f"Analyzing Regime Distribution for {symbol} ({start_date.date()} ~ {end_date.date()})")
    print(f"Total Days: {len(df)}")
    
    regime_counts = {}
    
    # Iterate and calculate regime for each day
    # Note: calculate_latest_micro_regime takes a history DF and calculates for the LAST row.
    # So we need to feed it expanding windows?
    # Or just re-implement the logic here for efficiency.
    
    # Calculate rolling metrics
    df['ret_5d'] = df['close'].pct_change(5)
    
    # ATR
    high = df['high']
    low = df['low']
    prev_close = df['close'].shift(1)
    tr = np.maximum(high - low, np.maximum(abs(high - prev_close), abs(low - prev_close)))
    df['atr'] = tr.rolling(14).mean()
    df['atr_pct'] = df['atr'] / df['close']
    
    regimes = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        if pd.isna(row['ret_5d']) or pd.isna(row['atr_pct']):
            regimes.append("MR_UNKNOWN")
            continue
            
        r = classify_micro_regime(row['ret_5d'], row['ret_5d'], row['atr_pct']) 
        # Wait, classify_micro_regime takes (ret_1d, ret_5d, atr_pct).
        # The first arg is ret_1d?
        # Let's check signature: classify_micro_regime(one_day_ret, five_day_ret, atr_pct)
        # But inside classify_micro_regime, it only uses five_day_ret and atr_pct!
        # "if five_day_ret > 0.03..."
        # So first arg is ignored? Let's pass ret_5d just in case or 0.
        
        r = classify_micro_regime(0, row['ret_5d'], row['atr_pct'])
        regimes.append(r)
        
    df['regime'] = regimes
    
    counts = df['regime'].value_counts()
    total = len(df)
    
    print("\nRegime Distribution:")
    for regime, count in counts.items():
        print(f"{regime}: {count} ({count/total*100:.1f}%)")
        
    # Check R3~R5 equivalents
    # Current mapping:
    # MR_UP_DRIFT (R2?)
    # MR_UP_SPIKE (R1?)
    # MR_FLAT_BOX (R3/R4?)
    # MR_FLAT_NOISY (R4?)
    # MR_GRIND_DOWN (R6?)
    # MR_PANIC_DOWN (R7?)
    
if __name__ == "__main__":
    main()
