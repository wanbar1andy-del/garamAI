"""
Verify Data Integrity in G Drive
"""
from pathlib import Path
import sys

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

def verify_data():
    # 1. Check Daily History
    print(f"Checking data in {PATHS.HISTORY_DIR}...")
    if PATHS.HISTORY_DIR.exists():
        files = list(PATHS.HISTORY_DIR.glob("*.csv"))
        print(f"Found {len(files)} Daily CSV files.")
    
    # 2. Check Minute History (G Drive)
    minute_dir = Path("g:/내 드라이브/garamdata/history/minute")
    print(f"\nChecking data in {minute_dir}...")
    
    target_file = minute_dir / "005930_1m.csv"
    if target_file.exists():
        print(f"Found {target_file.name} ({target_file.stat().st_size / 1024 / 1024:.1f} MB)")
        import pandas as pd
        df = pd.read_csv(target_file)
        print(f"Rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
        if 'date' in df.columns:
            print(f"Range: {df['date'].min()} ~ {df['date'].max()}")
        elif 'timestamp' in df.columns:
            print(f"Range: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    # 4. Full Inventory Summary
    print("\n=== Data Inventory Summary ===")
    
    # Daily
    daily_files = list(PATHS.HISTORY_DIR.glob("*.csv"))
    daily_size = sum(f.stat().st_size for f in daily_files) / 1024 / 1024
    print(f"Daily Data: {len(daily_files)} files, Total Size: {daily_size:.1f} MB")
    
    # Minute
    minute_dir = Path("g:/내 드라이브/garamdata/history/minute")
    if minute_dir.exists():
        minute_files = list(minute_dir.glob("*_1m.csv"))
        minute_size = sum(f.stat().st_size for f in minute_files) / 1024 / 1024
        print(f"Minute Data: {len(minute_files)} files, Total Size: {minute_size:.1f} MB")
        
        # Sample Range (005930)
        target = minute_dir / "005930_1m.csv"
        if target.exists():
            try:
                df = pd.read_csv(target)
                start = df.iloc[0]['date'] if 'date' in df.columns else df.index[0]
                end = df.iloc[-1]['date'] if 'date' in df.columns else df.index[-1]
                print(f"Sample (005930) Range: {start} ~ {end} ({len(df)} bars)")
            except:
                pass
    else:
        print("Minute Data: Directory not found")

if __name__ == "__main__":
    verify_data()
