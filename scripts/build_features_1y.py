from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np

from scripts._hero_common import now_ts, rsi_wilder, atr, zscore, ew_universe_return

def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".")
    p.add_argument("--config", default="config/feature_set.json")
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    cfg = load_config(project_root / args.config)

    daily_path = project_root / cfg.get("daily_path", "datasets/daily/daily_1y.csv")
    out_path = project_root / cfg.get("features_out", "datasets/features/features_1y.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rsi_windows = [int(x) for x in cfg.get("rsi_windows", [14])]
    return_periods = [int(x) for x in cfg.get("return_periods", [1, 3, 5, 10, 20])]
    ma_windows = [int(x) for x in cfg.get("ma_windows", [5, 20, 60])]
    atr_window = int(cfg.get("atr_window", 14))
    vol_ratio_window = int(cfg.get("vol_ratio_window", 20))
    zscore_window = int(cfg.get("zscore_window", 20))
    include_mkt = bool(cfg.get("include_market_ew_return", True))

    df = pd.read_csv(daily_path, dtype={"date": "string", "symbol": "string"})
    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    df["date"] = df["date"].astype(str)

    for c in ["open", "high", "low", "close", "volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    for p_ in return_periods:
        df[f"ret_{p_}"] = df.groupby("symbol")["close"].pct_change(p_)

    for w in ma_windows:
        ma = df.groupby("symbol")["close"].rolling(w, min_periods=w).mean().reset_index(level=0, drop=True)
        df[f"ma_{w}"] = ma

    df[f"zclose_ma{zscore_window}"] = df.groupby("symbol")["close"].apply(lambda s: zscore(s, zscore_window)).reset_index(level=0, drop=True)

    for w in rsi_windows:
        df[f"rsi_{w}"] = df.groupby("symbol")["close"].apply(lambda s: rsi_wilder(s, w)).reset_index(level=0, drop=True)

    df[f"atr_{atr_window}"] = df.groupby("symbol").apply(
        lambda g: atr(g["high"], g["low"], g["close"], atr_window)
    ).reset_index(level=0, drop=True)

    df["range_pct"] = (df["high"] - df["low"]) / df["close"].replace(0, np.nan)

    vol_ma = df.groupby("symbol")["volume"].rolling(vol_ratio_window, min_periods=vol_ratio_window).mean().reset_index(level=0, drop=True)
    df[f"vol_ratio_{vol_ratio_window}"] = df["volume"] / vol_ma.replace(0, np.nan)

    if include_mkt:
        mkt = ew_universe_return(df[["date", "symbol", "close"]])
        df = df.merge(mkt, on="date", how="left")

    key_cols = ["date", "symbol", "open", "high", "low", "close", "volume"]
    feat_cols = [c for c in df.columns if c not in key_cols]
    out = df[key_cols + feat_cols].copy()

    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] features written: {out_path}")
    print(f"- rows={len(out)} symbols={out['symbol'].nunique()} dates={out['date'].nunique()} ts={now_ts()}")

if __name__ == "__main__":
    main()
