from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

from scripts._hero_common import now_ts

def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 50:
        return float("nan")
    c = np.corrcoef(a, b)
    return float(c[0, 1])

def point_biserial_corr(x: pd.Series, y01: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y01, errors="coerce")
    m = x.notna() & y.notna()
    return _corr(x[m].values, y[m].values)

def info_coeff(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    m = x.notna() & y.notna()
    return _corr(x[m].values, y[m].values)

def lift_hero(x: pd.Series, hero: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    hero = pd.to_numeric(hero, errors="coerce").fillna(0)
    m = x.notna()
    xh = x[m & (hero == 1)]
    xn = x[m & (hero == 0)]
    if len(xh) < 10 or len(xn) < 10:
        return float("nan")
    return float(xh.mean() - xn.mean())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".")
    p.add_argument("--features", default="datasets/features/features_1y.csv")
    p.add_argument("--labels", required=True)
    p.add_argument("--out_dir", default="results/screening")
    p.add_argument("--top_n", type=int, default=30)
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    feat_path = project_root / args.features
    lab_path = project_root / args.labels
    out_dir = project_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    feat = pd.read_csv(feat_path, dtype={"date": "string", "symbol": "string"})
    lab = pd.read_csv(lab_path, dtype={"date": "string", "symbol": "string"})

    df = feat.merge(lab[["date", "symbol", "hero", "fwd_ret_H"]], on=["date", "symbol"], how="inner")
    if df.empty:
        raise SystemExit("[FAIL] merge(features, labels) produced empty set. Check date/symbol alignment.")

    hero_rate = float(df["hero"].mean())
    numeric_cols = [c for c in df.columns if c not in ("date", "symbol", "hero", "fwd_ret_H")]
    rows = []
    for c in numeric_cols:
        x = df[c]
        rows.append({
            "feature": c,
            "pb_corr_hero": point_biserial_corr(x, df["hero"]),
            "ic_fwd_ret": info_coeff(x, df["fwd_ret_H"]),
            "lift_mean_hero_minus_non": lift_hero(x, df["hero"]),
            "non_null": int(pd.to_numeric(x, errors="coerce").notna().sum()),
        })

    out = pd.DataFrame(rows).sort_values(["pb_corr_hero", "ic_fwd_ret"], ascending=False)
    ts = now_ts()
    out_path = out_dir / f"feature_screening_{Path(lab_path).stem}_{ts}.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"[OK] screening written: {out_path}")
    print(f"- merged_rows={len(df)} hero_rate={hero_rate:.4f} features={len(out)} topN={args.top_n} ts={ts}")
    print(out.head(args.top_n).to_string(index=False))

if __name__ == "__main__":
    main()
