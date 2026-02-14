from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from scripts._hero_common import now_ts

def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".")
    p.add_argument("--config", default="config/hero_labelling.json")
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    cfg = load_config(project_root / args.config)

    H = int(cfg.get("horizon_days", 5))
    N = int(cfg.get("top_n", 10))
    daily_path = project_root / cfg.get("daily_path", "datasets/daily/daily_1y.csv")
    out_tpl = cfg.get("labels_out", "datasets/labels/hero_labels_H{H}_top{N}_1y.csv")
    out_path = project_root / out_tpl.format(H=H, N=N)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    min_price = float(cfg.get("min_price", 0))
    min_avg_vol20 = float(cfg.get("min_avg_volume_20d", 0))

    df = pd.read_csv(daily_path, dtype={"date": "string", "symbol": "string"})
    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    df["date"] = df["date"].astype(str)
    df = df.sort_values(["symbol", "date"])

    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0.0)

    df["fwd_close"] = df.groupby("symbol")["close"].shift(-H)
    df["fwd_ret_H"] = (df["fwd_close"] / df["close"]) - 1.0

    df["avg_vol_20d"] = df.groupby("symbol")["volume"].rolling(20, min_periods=20).mean().reset_index(level=0, drop=True)

    tradable = (df["close"] >= min_price) & (df["avg_vol_20d"].fillna(0.0) >= min_avg_vol20)

    d = df.loc[tradable & df["fwd_ret_H"].notna(), ["date", "symbol", "fwd_ret_H"]].copy()
    if d.empty:
        raise SystemExit("[FAIL] No tradable rows with forward return. Check filters or daily data span.")

    d["cs_rank"] = d.groupby("date")["fwd_ret_H"].rank(ascending=False, method="first").astype(int)
    d["hero"] = (d["cs_rank"] <= N).astype(int)

    d = d.sort_values(["date", "cs_rank"])
    d.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] labels written: {out_path}")
    print(f"- H={H} topN={N} dates={d['date'].nunique()} heroes_total={int(d['hero'].sum())} ts={now_ts()}")

if __name__ == "__main__":
    main()
