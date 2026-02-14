from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

from scripts._hero_common import now_ts

def apply_rule_mask(df: pd.DataFrame, rule_str: str) -> pd.Series:
    rule_str = rule_str.strip()
    parts = [p.strip() for p in rule_str.split("&")]
    m = pd.Series(True, index=df.index)
    for p in parts:
        if "<=" in p:
            f, t = p.split("<=", 1)
            x = pd.to_numeric(df[f.strip()], errors="coerce")
            m = m & (x <= float(t))
        elif ">=" in p:
            f, t = p.split(">=", 1)
            x = pd.to_numeric(df[f.strip()], errors="coerce")
            m = m & (x >= float(t))
        else:
            return pd.Series(False, index=df.index)
    return m.fillna(False)

def eval_rule_on_slice(df: pd.DataFrame, rule_str: str, min_spd: int, max_spd: int) -> dict:
    mask = apply_rule_mask(df, rule_str)
    d = df.loc[mask, ["date", "hero", "fwd_ret_H"]].copy()
    if d.empty:
        return {"signals": 0, "days": 0, "signals_per_day": 0.0, "avg_fwd_ret": np.nan, "precision_hero": np.nan}
    by_day = d.groupby("date").size()
    spd = float(by_day.mean())
    if spd < min_spd or spd > max_spd:
        return {"signals": int(len(d)), "days": int(by_day.shape[0]), "signals_per_day": spd,
                "avg_fwd_ret": np.nan, "precision_hero": np.nan}
    return {"signals": int(len(d)), "days": int(by_day.shape[0]), "signals_per_day": spd,
            "avg_fwd_ret": float(pd.to_numeric(d["fwd_ret_H"], errors="coerce").mean()),
            "precision_hero": float(pd.to_numeric(d["hero"], errors="coerce").mean())}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".")
    p.add_argument("--features", default="datasets/features/features_1y.csv")
    p.add_argument("--labels", required=True)
    p.add_argument("--rules_csv", required=True)
    p.add_argument("--train_months", type=int, default=9)
    p.add_argument("--test_months", type=int, default=3)
    p.add_argument("--stride_months", type=int, default=1)
    p.add_argument("--select_top_k", type=int, default=20)
    p.add_argument("--min_spd", type=int, default=3)
    p.add_argument("--max_spd", type=int, default=25)
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    feat = pd.read_csv(project_root / args.features, dtype={"date": "string", "symbol": "string"})
    lab = pd.read_csv(project_root / args.labels, dtype={"date": "string", "symbol": "string"})
    rules = pd.read_csv(project_root / args.rules_csv)

    df = feat.merge(lab[["date", "symbol", "hero", "fwd_ret_H"]], on=["date", "symbol"], how="inner")
    df["month"] = df["date"].astype(str).str.slice(0, 6)

    months = sorted(df["month"].unique().tolist())
    need = args.train_months + args.test_months
    if len(months) < need:
        raise SystemExit(f"[FAIL] Not enough months for walkforward. have={len(months)} need>={need}")

    rows = []
    for start in range(0, len(months) - need + 1, args.stride_months):
        train_ms = months[start:start + args.train_months]
        test_ms = months[start + args.train_months:start + need]

        d_train = df[df["month"].isin(train_ms)]
        d_test = df[df["month"].isin(test_ms)]

        cand = rules.copy()
        train_scores = []
        for r in cand["rule"].astype(str).tolist():
            m = eval_rule_on_slice(d_train, r, args.min_spd, args.max_spd)
            train_scores.append(m.get("avg_fwd_ret", np.nan))
        cand["train_avg_fwd_ret"] = train_scores
        cand = cand.dropna(subset=["train_avg_fwd_ret"]).sort_values("train_avg_fwd_ret", ascending=False).head(args.select_top_k)

        for _, row in cand.iterrows():
            r = str(row["rule"])
            te = eval_rule_on_slice(d_test, r, args.min_spd, args.max_spd)
            rows.append({
                "train_start": train_ms[0], "train_end": train_ms[-1],
                "test_start": test_ms[0], "test_end": test_ms[-1],
                "rule": r,
                "train_avg_fwd_ret": float(row["train_avg_fwd_ret"]),
                "test_avg_fwd_ret": te["avg_fwd_ret"],
                "test_precision_hero": te["precision_hero"],
                "test_signals": te["signals"],
                "test_signals_per_day": te["signals_per_day"],
            })

    out = pd.DataFrame(rows)
    ts = now_ts()
    out_path = project_root / "results" / "walkforward" / f"wf_report_{Path(args.labels).stem}_{ts}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    agg = out.groupby("rule").agg(
        n_splits=("test_avg_fwd_ret", "count"),
        mean_test_ret=("test_avg_fwd_ret", "mean"),
        mean_test_prec=("test_precision_hero", "mean"),
        mean_spd=("test_signals_per_day", "mean"),
    ).sort_values("mean_test_ret", ascending=False).head(20)

    print(f"[OK] walkforward written: {out_path}")
    print("\n=== TOP RULES (WF) ===")
    print(agg.to_string())

if __name__ == "__main__":
    main()
