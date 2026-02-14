import pandas as pd
from garam_core.data.loader import load_ohlcv
from pathlib import Path
from datetime import timedelta

project_root = Path(__file__).resolve().parents[2]
data_root = project_root / "GARAM_Data"

df = load_ohlcv(data_root, "005930", "minute")
df = df.reset_index()
if "date" not in df.columns: df.rename(columns={"index": "date"}, inplace=True)
df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

target_date = pd.Timestamp("2025-12-15")
scan_ts = target_date + timedelta(hours=15, minutes=20)

print(f"Checking {scan_ts}...")
idx = df["date"].searchsorted(scan_ts)
if idx < len(df):
    row = df.iloc[idx]
    print(f"Found: {row['date']}, Close: {row['close']}, Vol: {row['volume']}")
    if row['date'] > scan_ts:
        print("Tip: Found is FUTURE of scan_ts. Checking Prev.")
        if idx > 0:
            row_prev = df.iloc[idx-1]
            print(f"Prev: {row_prev['date']}, Close: {row_prev['close']}, Vol: {row_prev['volume']}")

# Check Vol Accel Manually
# Window 15:11 ~ 15:20
ts_start = scan_ts - timedelta(minutes=9)
subset = df[(df["date"] >= ts_start) & (df["date"] <= scan_ts)]
print(f"Subset Len: {len(subset)}")
if not subset.empty:
    vol_sum = subset["volume"].sum()
    vol_ma = vol_sum / 10.0
    curr_vol = subset.iloc[-1]["volume"]
    print(f"Vol Sum: {vol_sum}, Vol MA: {vol_ma}, Current: {curr_vol}")
    if vol_ma > 0:
        print(f"Vol Accel: {curr_vol / vol_ma}")

# Check ROC 5m
ts_5m = scan_ts - timedelta(minutes=5)
# Find closest
idx_5 = df["date"].searchsorted(ts_5m)
if idx_5 < len(df):
    row_5 = df.iloc[idx_5]
    print(f"5m Ago: {row_5['date']}, Close: {row_5['close']}")
    
    curr_close = subset.iloc[-1]["close"]
    roc = (curr_close / row_5["close"]) - 1.0
    print(f"ROC 5m: {roc:.4f}")
