from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from scripts._hero_common import now_ts

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".")
    p.add_argument("--labels", required=True, help="datasets/labels/hero_labels_*.csv")
    p.add_argument("--top_n", type=int, default=10, help="How many heroes per day to print/export")
    p.add_argument("--out_dir", default="results")
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    lab_path = project_root / args.labels
    out_dir = project_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(lab_path, dtype={"date":"string","symbol":"string"})
    df["date"] = df["date"].astype(str)
    df["symbol"] = df["symbol"].astype(str).str.zfill(6)

    # ensure rank if exists
    if "cs_rank" in df.columns:
        df = df.sort_values(["date","cs_rank"])
    else:
        df = df.sort_values(["date","fwd_ret_H"], ascending=[True, False])

    # daily hero list
    daily = df[df.get("hero", 0) == 1].copy()
    if daily.empty:
        raise SystemExit("[FAIL] No hero rows found in labels.")

    # keep top_n per day
    daily["rank_in_day"] = daily.groupby("date").cumcount() + 1
    daily = daily[daily["rank_in_day"] <= int(args.top_n)]

    # export wide report: date, hero1..heroN
    pivot = daily.pivot_table(index="date", columns="rank_in_day", values="symbol", aggfunc="first")
    pivot = pivot.rename(columns={i: f"hero_{i}" for i in pivot.columns}).reset_index()

    ts = now_ts()
    out_path = out_dir / f"daily_heroes_{lab_path.stem}_{ts}.csv"
    pivot.to_csv(out_path, index=False, encoding="utf-8-sig")

    # stability metrics
    hero_cols = [c for c in pivot.columns if c.startswith("hero_")]
    pivot["set_sig"] = pivot[hero_cols].astype(str).agg("|".join, axis=1)
    pivot["changed"] = (pivot["set_sig"] != pivot["set_sig"].shift(1)).astype(int)
    change_rate = float(pivot["changed"].mean())

    print(f"[OK] daily hero report: {out_path}")
    print(f"- days={len(pivot)} top_n={args.top_n} change_rate={change_rate:.3f} ts={ts}")
    print(pivot.head(5).to_string(index=False))

if __name__ == "__main__":
    main()
