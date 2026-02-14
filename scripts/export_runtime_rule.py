from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from scripts._hero_common import now_ts

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".")
    p.add_argument("--wf_report", required=True)
    p.add_argument("--top_n", type=int, default=3)
    p.add_argument("--out", default="config/runtime_rule.json")
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    wf = pd.read_csv(project_root / args.wf_report)

    g = wf.groupby("rule").agg(
        n_splits=("test_avg_fwd_ret", "count"),
        mean_test_ret=("test_avg_fwd_ret", "mean"),
        mean_test_prec=("test_precision_hero", "mean"),
        mean_spd=("test_signals_per_day", "mean"),
    ).reset_index()

    g = g.dropna(subset=["mean_test_ret"]).sort_values("mean_test_ret", ascending=False).head(args.top_n)

    pack = {"generated_at": now_ts(), "source": str(args.wf_report), "top_n": int(args.top_n), "rules": []}
    for _, r in g.iterrows():
        pack["rules"].append({
            "rule": str(r["rule"]),
            "n_splits": int(r["n_splits"]),
            "mean_test_avg_fwd_ret": float(r["mean_test_ret"]),
            "mean_test_precision_hero": float(r["mean_test_prec"]),
            "mean_test_signals_per_day": float(r["mean_spd"]),
        })

    out_path = project_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] runtime rulepack written: {out_path}")
    print(json.dumps(pack, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
