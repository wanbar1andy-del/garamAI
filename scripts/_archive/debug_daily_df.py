import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# from config import PATHS

def debug_daily_df():
    symbol = "005930"
    # file_path = PATHS.BASE_DIR / "analysis/regimes" / f"intraday_with_regime_{symbol}.csv"
    file_path = Path(r"c:\garam\garam\analysis\regimes\intraday_with_regime_005930.csv")
    
    print(f"Loading {file_path}...")
    df = pd.read_csv(file_path)
    
    # Parse timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
    print(f"Loaded {len(df)} rows.")
    
    # Resample
    resampled = df.resample('D').last()
    print("Resampled Head (Before DropNA):")
    print(resampled.head())
    print("Resampled Tail (Before DropNA):")
    print(resampled.tail())
    
    daily_df = resampled.dropna(how='all') # Only drop if ALL columns are NaN (e.g. weekends)
    # daily_df = resampled.dropna() # This was the culprit?
    
    daily_df.index = pd.to_datetime(daily_df.index).normalize()
    if daily_df.index.tz is not None:
        daily_df.index = daily_df.index.tz_localize(None)
        
    print(f"Daily DF Shape: {daily_df.shape}")
    print(f"Daily DF Index Dtype: {daily_df.index.dtype}")
    print(f"Daily DF Index Sample: {daily_df.index[:5]}")
    
    # Test Comparison
    target_date = datetime(2025, 10, 17).date()
    target_ts = pd.Timestamp(target_date)
    print(f"Target Date: {target_date}")
    print(f"Target Timestamp: {target_ts}")
    
    mask = daily_df.index < target_ts
    print(f"Mask Sum: {mask.sum()}")
    
    if mask.any():
        prev_daily = daily_df[mask].iloc[-1]
        print(f"Prev Daily Index: {prev_daily.name}")
        print(f"Prev Daily Trend: {prev_daily.get('trend_20d')}")
    else:
        print("Mask is empty!")

if __name__ == "__main__":
    debug_daily_df()
