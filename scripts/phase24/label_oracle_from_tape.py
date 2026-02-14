import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import sys

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from garam_core.data.loader import load_ohlcv

def _load_minute_df(data_root: Path, symbol: str) -> pd.DataFrame:
    df = load_ohlcv(data_root, symbol, "minute")
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    if "index" in df.columns and "date" not in df.columns:
        df.rename(columns={"index": "date"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)
    return df

def _price_at(close_s: pd.Series, ts: pd.Timestamp):
    if ts in close_s.index:
        return float(close_s.loc[ts])
    idx = close_s.index.searchsorted(ts, side="right") - 1
    if idx < 0:
        return np.nan
    return float(close_s.iloc[idx])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tape_csv", required=True, help="Result of build_decision_tape")
    ap.add_argument("--horizons", type=str, default="10,30,60")
    ap.add_argument("--out_tag", type=str, default="p24_oracle_tape_match")
    ap.add_argument("--cost_rt", type=float, default=0.0030)
    args = ap.parse_args()

    horizons = [int(x.strip()) for x in args.horizons.split(",") if x.strip()]
    if not horizons:
        raise ValueError("horizons empty")

    df_t = pd.read_csv(args.tape_csv, dtype={"symbol": str})
    df_t["ts"] = pd.to_datetime(df_t["ts"])

    # Extract ALL unique (ts, symbol) pairs regardless of rank
    targets = df_t[["ts", "symbol"]].drop_duplicates()
    
    # Filter out invalid symbols (NaN, empty, "nan")
    targets = targets.dropna(subset=["symbol"])
    targets = targets[targets["symbol"].astype(str).str.strip() != ""]
    targets = targets[targets["symbol"].astype(str).str.lower() != "nan"]
    
    symbols = targets["symbol"].unique().tolist()
    
    # Preload data
    data_root = project_root / "GARAM_Data"
    data_map = {}
    print(f"[INFO] Loading data for {len(symbols)} unique symbols in tape...")
    for i, sym in enumerate(symbols, 1):
        if i % 100 == 0:
            print(f"[LOAD] {i}/{len(symbols)}")
        df = _load_minute_df(data_root, sym)
        if not df.empty:
            data_map[sym] = df.set_index("date")["close"]

    rows = []
    
    # Process
    # To optimize: Group by symbol to avoid random access to data_map (though dict lookup is fast)
    # Actually, iterate by row in targets is fine if len(targets) isn't huge.
    # But better: Iterate symbols, then find all TS for that symbol.
    
    grouped = targets.groupby("symbol")
    
    count = 0
    total = len(targets)
    
    for sym, group in grouped:
        if sym not in data_map:
            # Data missing completely
            for ts in group["ts"]:
                for H in horizons:
                     rows.append({
                        "ts": ts,
                        "horizon_min": H,
                        "symbol": sym,
                        "raw_ret": np.nan,
                        "net_ret": np.nan,
                        "note": "NO_DATA"
                    })
            continue
            
        close_s = data_map[sym]
        
        for ts in group["ts"]:
            p0 = _price_at(close_s, ts)
            
            for H in horizons:
                if not (np.isfinite(p0) and p0 > 0):
                     rows.append({
                        "ts": ts,
                        "horizon_min": H,
                        "symbol": sym,
                        "raw_ret": np.nan,
                        "net_ret": np.nan,
                        "note": "BAD_P0"
                     })
                     continue

                ts_exit = ts + pd.Timedelta(minutes=H)
                p1 = _price_at(close_s, ts_exit)
                
                if not (np.isfinite(p1) and p1 > 0):
                     rows.append({
                        "ts": ts,
                        "horizon_min": H,
                        "symbol": sym,
                        "raw_ret": np.nan,
                        "net_ret": np.nan,
                        "note": "BAD_P1"
                     })
                     continue
                
                raw = (p1 / p0) - 1.0
                net = raw - args.cost_rt
                
                rows.append({
                    "ts": ts,
                    "horizon_min": H,
                    "symbol": sym,
                    "raw_ret": raw,
                    "net_ret": net,
                    "note": "OK"
                })
        
        count += len(group)
        if count % 1000 == 0:
            print(f"[PROG] {count}/{total} pairs processed")

    out_base = project_root / "results" / "phase24" / "oracle" / args.out_tag
    out_base.mkdir(parents=True, exist_ok=True)
    
    df_out = pd.DataFrame(rows)
    # Sort for deterministic output
    if not df_out.empty:
        df_out = df_out.sort_values(["ts", "horizon_min", "symbol"])
        
    # We also want to merge the "Universe Top1" if we want to calculate Regret correctly.
    # Ah, Regret = OracleTop1 - PolicyNet.
    # This script only calculates PolicyNet (since we only looked at tape symbols).
    # **** CRITICAL ****: Regret Calculation requires Oracle Top1 (Global).
    # The user says: "Oracle is TopK=400 (All)". If we already have that (p24_calib_5d_all),
    # we can just use it for "OracleTop1".
    # The PROBLEM was "Policy Symbol" was missing from the "TopK Oracle" file if it wasn't TopK.
    # So we need TWO files for Regret Report:
    # 1. Global Oracle (for Top1 benchmark) -> We assume the previous run `p24_calib_5d` (TopK=400) is close enough to Global Top1.
    # 2. Tape Oracle (for Policy realization) -> THIS script.
    
    # So this script produces `oracle_tape_match.csv`.
    
    start_date = df_t["ts"].min().strftime("%Y-%m-%d")
    end_date = df_t["ts"].max().strftime("%Y-%m-%d")
    out_csv = out_base / f"oracle_tape_match_{start_date}_{end_date}.csv"
    
    df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] {out_csv}")

if __name__ == "__main__":
    main()
