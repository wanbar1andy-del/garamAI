from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from scripts._hero_common import normalize_ohlcv_columns, now_ts

"""
Intraday Hero Labeling v1

정의: 매 시점 ts (5분 앵커)에서 향후 H분 동안 net_ret 상위 Top-K를 히어로로 라벨
목적: "그 순간의 히어로"를 분 단위로 기록 → 룰 마이닝 입력
"""

def parse_ts_to_time(ts_str: str) -> int:
    """YYYYMMDDHHMMSS -> HHMMSS as int"""
    return int(ts_str[-6:])

def is_trading_hours(ts_str: str, start_time: int = 90000, end_time: int = 152000) -> bool:
    """Check if timestamp is within trading hours"""
    t = parse_ts_to_time(ts_str)
    return start_time <= t <= end_time

def generate_anchors(df: pd.DataFrame, anchor_step: int) -> list[str]:
    """
    Generate anchor timestamps (5-min intervals).
    df must have 'date' column (YYYYMMDDHHMMSS).
    """
    df = df.copy()
    df["date"] = df["date"].astype(str)
    df["dt"] = pd.to_datetime(df["date"], format="%Y%m%d%H%M%S", errors="coerce")
    df = df.dropna(subset=["dt"])
    
    min_dt = df["dt"].min()
    max_dt = df["dt"].max()
    
    anchors = []
    current = min_dt.replace(second=0, microsecond=0)
    # Round to nearest anchor_step
    minute_offset = current.minute % anchor_step
    if minute_offset != 0:
        current = current + timedelta(minutes=anchor_step - minute_offset)
    
    while current <= max_dt:
        ts_str = current.strftime("%Y%m%d%H%M%S")
        if is_trading_hours(ts_str):
            anchors.append(ts_str)
        current = current + timedelta(minutes=anchor_step)
    
    return anchors

def load_minute_data(csv_path: Path, lookback_days: int = 365) -> pd.DataFrame:
    """Load minute bars with date filter"""
    if not csv_path.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(csv_path, dtype={"date": "string"})
    df = normalize_ohlcv_columns(df)
    
    if "close" not in df.columns or "date" not in df.columns:
        return pd.DataFrame()
    
    df["date"] = df["date"].astype(str)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    
    # Sort descending (newest first, as per ingest)
    df = df.sort_values("date", ascending=False)
    
    # Filter by lookback
    cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d")
    df = df[df["date"].str[:8] >= cutoff_date]
    
    # Reverse to ascending (oldest first for forward calculation)
    df = df.sort_values("date", ascending=True).reset_index(drop=True)
    
    return df[["date", "close", "volume"]].copy()

def compute_labels_for_symbol(
    sym: str,
    df: pd.DataFrame,
    anchors: list[str],
    H: int,
    cost_bps: float,
    min_volume_5m: float
) -> pd.DataFrame:
    """
    Compute hero labels for one symbol.
    Returns: DataFrame with columns [ts, symbol, close_t, close_tH, raw_ret, net_ret, vol_5m, valid]
    """
    if df.empty:
        return pd.DataFrame()
    
    df = df.set_index("date")
    
    rows = []
    for ts in anchors:
        if ts not in df.index:
            continue
        
        close_t = df.loc[ts, "close"]
        
        # Compute ts+H
        try:
            ts_dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
            ts_h_dt = ts_dt + timedelta(minutes=H)
            ts_h = ts_h_dt.strftime("%Y%m%d%H%M%S")
        except Exception:
            continue
        
        if ts_h not in df.index:
            continue  # Missing future data
        
        close_tH = df.loc[ts_h, "close"]
        
        # Validity checks
        if pd.isna(close_t) or pd.isna(close_tH):
            continue
        if close_t <= 0 or close_tH <= 0:
            continue
        
        
        # Volume check (5-min window)
        try:
            idx_t = df.index.get_loc(ts)
            if "volume" in df.columns:
                vol_5m = df.iloc[max(0, idx_t-4):idx_t+1]["volume"].sum()
            else:
                vol_5m = 0
        except Exception:
            vol_5m = 0
        
        valid = 1 if vol_5m >= min_volume_5m else 0
        
        # Returns
        raw_ret = (close_tH / close_t) - 1.0
        net_ret = raw_ret - (cost_bps / 10000.0)
        
        rows.append({
            "ts": ts,
            "symbol": sym,
            "close_t": float(close_t),
            "close_tH": float(close_tH),
            "raw_ret": float(raw_ret),
            "net_ret": float(net_ret),
            "vol_5m": float(vol_5m),
            "valid": int(valid)
        })
    
    return pd.DataFrame(rows)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".", help="Project root")
    p.add_argument("--config", default="config/hero_labelling_intraday.json")
    p.add_argument("--lookback_days", type=int, default=365)
    p.add_argument("--limit", type=int, default=None, help="Limit symbols for testing")
    p.add_argument("--universe_csv", default="GARAM_Data/real_universe_400.csv")
    p.add_argument("--minute_dir", default="GARAM_Data/history/minute")
    p.add_argument("--out_dir", default="datasets/intraday")
    args = p.parse_args()
    
    project_root = Path(args.project_root).resolve()
    config_path = project_root / args.config
    
    # Load config
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    anchor_step = cfg.get("anchor_step_minutes", 5)
    horizons = cfg.get("horizons", [15, 30, 60])
    top_k = cfg.get("top_k", 5)
    cost_bps = cfg["cost_model"]["total_bps"]
    min_volume_5m = cfg["filters"]["min_volume_5m"]
    min_net_ret = cfg["filters"]["min_net_ret"]
    
    # Load universe
    universe_path = project_root / args.universe_csv
    df_univ = pd.read_csv(universe_path)
    col = None
    for c in ["Code", "code", "symbol"]:
        if c in df_univ.columns:
            col = c
            break
    if col is None:
        raise SystemExit("Universe CSV has no recognizable symbol column")
    
    symbols = df_univ[col].astype(str).str.strip().str.zfill(6).tolist()
    symbols = [s for s in symbols if s.isdigit() and len(s) == 6]
    symbols = sorted(set(symbols))
    
    if args.limit:
        symbols = symbols[:args.limit]
    
    minute_dir = project_root / args.minute_dir
    out_dir = project_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[Intraday Hero Labeling] symbols={len(symbols)} horizons={horizons} anchor_step={anchor_step}min")
    
    # Determine anchors (use first symbol with data)
    anchors = []
    for sym in symbols[:10]:  # Sample from first 10
        csv_path = minute_dir / f"{sym}.csv"
        df_sample = load_minute_data(csv_path, lookback_days=args.lookback_days)
        if not df_sample.empty:
            anchors = generate_anchors(df_sample, anchor_step)
            break
    
    if not anchors:
        raise SystemExit("[FAIL] Could not generate anchors from any symbol")
    
    print(f"- Anchors generated: {len(anchors)} (from {anchors[0]} to {anchors[-1]})")
    
    # Process each horizon
    for H in horizons:
        print(f"\n[H={H}] Processing...")
        
        all_rows = []
        bad = 0
        
        for idx, sym in enumerate(symbols):
            csv_path = minute_dir / f"{sym}.csv"
            df_min = load_minute_data(csv_path, lookback_days=args.lookback_days)
            
            if df_min.empty:
                bad += 1
                continue
            
            df_sym = compute_labels_for_symbol(
                sym=sym,
                df=df_min,
                anchors=anchors,
                H=H,
                cost_bps=cost_bps,
                min_volume_5m=min_volume_5m
            )
            
            if not df_sym.empty:
                all_rows.append(df_sym)
            
            if (idx + 1) % 50 == 0:
                print(f"  - Processed {idx+1}/{len(symbols)} symbols...")
        
        if not all_rows:
            print(f"[WARN] H={H}: No data. Skipping.")
            continue
        
        # Combine all symbols
        df_all = pd.concat(all_rows, ignore_index=True)
        df_all["date"] = df_all["ts"].str[:8]
        
        # Rank within each timestamp (cross-sectional)
        df_all = df_all.sort_values(["ts", "net_ret"], ascending=[True, False])
        df_all["rank"] = df_all.groupby("ts").cumcount() + 1
        df_all["pct_rank"] = df_all.groupby("ts")["net_ret"].rank(pct=True)
        
        # Hero label
        df_all["hero"] = 0
        valid_mask = (df_all["valid"] == 1) & (df_all["net_ret"] >= min_net_ret)
        df_all.loc[valid_mask & (df_all["rank"] <= top_k), "hero"] = 1
        
        # Reorder columns
        cols_order = ["ts", "date", "symbol", "close_t", "close_tH", "raw_ret", "net_ret", 
                      "rank", "pct_rank", "hero", "valid", "vol_5m"]
        df_all = df_all[cols_order]
        
        # Save
        out_path = out_dir / f"labels_1y_H{H}.parquet"
        df_all.to_parquet(out_path, index=False, compression="snappy")
        
        heroes = (df_all["hero"] == 1).sum()
        valids = (df_all["valid"] == 1).sum()
        
        print(f"[OK] H={H} saved: {out_path}")
        print(f"  - rows={len(df_all)} heroes={heroes} valid={valids} bad_symbols={bad}")
        print(f"  - timestamps={df_all['ts'].nunique()} hero_rate={heroes/len(df_all)*100:.2f}%")
    
    print(f"\n[DONE] {now_ts()}")

if __name__ == "__main__":
    main()
