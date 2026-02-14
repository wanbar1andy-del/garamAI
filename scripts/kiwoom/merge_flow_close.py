import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import sys

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from garam_core.data.loader import load_ohlcv

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True, help="e.g. 005930")
    ap.add_argument("--flow_csv", required=True, help="Kiwoom exported program flow csv")
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args()

    sym = args.symbol
    df_f = pd.read_csv(args.flow_csv, dtype={"일자": str})
    df_f["date"] = pd.to_datetime(df_f["일자"], format="%Y%m%d")

    # Load minute OHLCV and compute daily close + daily turnover
    data_root = project_root / "GARAM_Data"
    
    # Try loading minute data first (SSOT preference)
    # If using sim data, we might need a different loader or path.
    # Assuming 'GARAM_Data/history/minute/005930.csv' or via loader
    try:
        df_m = load_ohlcv(data_root, sym, "minute")
    except Exception as e:
        df_m = None
        print(f"[WARN] load_ohlcv failed: {e}")

    if df_m is None or df_m.empty:
        # Fallback to direct CSV read if loader fails or returns empty (e.g. daily limit check)
        # But 'load_ohlcv' is the SSOT.
        raise RuntimeError(f"minute OHLCV missing: {sym}")

    df_m = df_m.reset_index()
    if "index" in df_m.columns and "date" not in df_m.columns:
        df_m.rename(columns={"index": "date"}, inplace=True)
    df_m.columns = [c.lower() for c in df_m.columns]
    
    if "date" not in df_m.columns:
         # Sometimes index is the date
         pass # Handled by reset_index above usually
         
    df_m["date"] = pd.to_datetime(df_m["date"]).dt.tz_localize(None)
    df_m = df_m.sort_values("date")

    df_m["day"] = df_m["date"].dt.normalize()
    daily_close = df_m.groupby("day")["close"].last().rename("종가")
    
    # 일별 거래대금(근사): sum(close*volume) - improved accuracy if minute-based
    daily_turnover = (df_m["close"] * df_m["volume"]).groupby(df_m["day"]).sum().rename("turnover")

    df_p = pd.concat([daily_close, daily_turnover], axis=1).reset_index().rename(columns={"day": "date"})
    
    # Left join to Flow Data (Flow is the master here)
    df = df_f.merge(df_p, on="date", how="left")

    # 프로그램 순매수금액이 어떤 단위든(원/천원/백만원) 일단 turnover 대비 비율로 normalize
    # (단위 불확실성 흡수 목적)
    df["prog_amt"] = pd.to_numeric(df["프로그램순매수금액"], errors="coerce")
    df["prog_qty"] = pd.to_numeric(df["프로그램순매수수량"], errors="coerce")
    
    # Avoid division by zero
    df["prog_amt_ratio"] = df["prog_amt"] / df["turnover"].replace(0, np.nan)

    # 20일 zscore (안정적 보정용)
    s = df.sort_values("date")["prog_amt_ratio"]
    mu = s.rolling(20, min_periods=5).mean()
    sd = s.rolling(20, min_periods=5).std().replace(0, np.nan)
    df["prog_amt_ratio_z20"] = (s - mu) / sd

    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # Save clean English columns primarily, but keep Korean if useful for debugging
    # Dropping redundant 'date' (kept from merge key)
    # The user script dropped 'date' but kept '일자'.
    # I'll keep 'date' for easier pandas usage later, or stick to user preference.
    # User: `df.drop(columns=["date"]).to_csv(...)`
    # Okay, respecting user script.
    
    df.drop(columns=["date"]).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"[OK] {out} rows={len(df)}")

if __name__ == "__main__":
    main()
