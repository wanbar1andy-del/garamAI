import pandas as pd
import numpy as np
from pathlib import Path
import glob

def parse_minute_csv(filepath):
    try:
        df = pd.read_csv(filepath)
        cols = [c.lower() for c in df.columns]
        df.columns = cols
        if "datetime" in df.columns: df = df.rename(columns={"datetime": "date"})
        if "volume" not in df.columns: df["volume"] = 0.0
        
        if "date" in df.columns:
             df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
             if df["dt"].isnull().all():
                 df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M", errors='coerce')
        
        df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
        return df[["close", "volume"]]
    except:
        return pd.DataFrame()

def main():
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    # Load 1 symbol
    files = glob.glob(str(data_dir / "*.csv"))
    if not files:
        print("No files found")
        return
        
    f = files[0]
    print(f"Loading {f}...")
    df = parse_minute_csv(f)
    print(f"Loaded {len(df)} rows. Range: {df.index.min()} to {df.index.max()}")
    
    # Filter range (same as backtest)
    s_dt = pd.to_datetime("20250601")
    e_dt = pd.to_datetime("20251212")
    df = df[(df.index >= s_dt) & (df.index <= e_dt)]
    print(f"Filtered {len(df)} rows.")
    
    if df.empty:
        print("Empty after filter")
        return

    closes = df[["close"]]
    volumes = df[["volume"]]
    
    # Run Logic
    print("--- Logic Check ---")
    c_daily = closes.resample('D').last().ffill()
    print(f"Daily Rows: {len(c_daily)}")
    ma60 = c_daily.rolling(window=60).mean().shift(1)
    print(f"MA60 Non-Null: {ma60.notnull().sum().sum()}")
    
    c_5m = closes.resample('5min', label='right').last()
    v_5m = volumes.resample('5min', label='right').sum()
    print(f"5m Rows: {len(c_5m)}")
    
    rolling = c_5m.rolling(window=20)
    mid = rolling.mean()
    std = rolling.std()
    bb_width = (mid + 2*std - (mid - 2*std)) / (mid + 1e-9)
    print(f"BB Width Non-Null: {bb_width.notnull().sum().sum()}")
    print(f"BB Width Mean: {bb_width.mean().item()}")
    
    width_mean = bb_width.rolling(window=100).mean()
    width_std = bb_width.rolling(window=100).std()
    width_z = (bb_width - width_mean) / (width_std + 1e-9)
    print(f"Width Z Non-Null: {width_z.notnull().sum().sum()}")
    print(f"Width Z Min: {width_z.min().item()}, Max: {width_z.max().item()}")
    
    is_squeezed = (width_z < 0.5)
    print(f"Squeezed Count (Z < 0.5): {is_squeezed.sum().sum()}")
    
    v_ma20 = v_5m.rolling(window=20).mean()
    is_vol_exploded = (v_5m > 1.5 * v_ma20) & (v_ma20 > 0)
    print(f"Vol Exploded Count (>1.5x): {is_vol_exploded.sum().sum()}")
    
    was_squeezed = is_squeezed.rolling(window=3).max().fillna(0)
    coiling = (was_squeezed > 0) & is_vol_exploded
    print(f"Coiling Count: {coiling.sum().sum()}")

    ma60_aligned = ma60.reindex(closes.index, method='ffill')
    is_above = (closes > ma60_aligned)
    print(f"Above MA60 Count: {is_above.sum().sum()}")
    
    final = coiling.reindex(closes.index, method='ffill').fillna(False) & is_above
    print(f"Final (Coiling & Above): {final.sum().sum()}")

if __name__ == "__main__":
    main()
