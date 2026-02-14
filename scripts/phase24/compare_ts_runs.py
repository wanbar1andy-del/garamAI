# scripts/phase24/compare_ts_runs.py
# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline_log", required=True)
    ap.add_argument("--boost_log", required=True)
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args()

    a = pd.read_csv(Path(args.baseline_log), encoding="utf-8-sig")
    b = pd.read_csv(Path(args.boost_log), encoding="utf-8-sig")

    key = ["ts"]
    a = a.add_prefix("a_")
    b = b.add_prefix("b_")

    df = a.merge(b, left_on="a_ts", right_on="b_ts", how="inner")

    # decision flip
    df["flip"] = (df["a_switch"] != df["b_switch"]).astype(int)

    # “경계 근처” 진단: baseline 기준 margin = diff - gap_effective(=gap_base)
    # boost 기준 margin = diff - gap_effective(=gap_base+boost)
    df["a_margin"] = df["a_diff_best_minus_current"] - df["a_gap_effective"]
    df["b_margin"] = df["b_diff_best_minus_current"] - df["b_gap_effective"]

    # 요약
    summary = {
        "rows": len(df),
        "flips": int(df["flip"].sum()),
        "flip_rate": float(df["flip"].mean()) if len(df) else 0.0,
        "blocked_cap_baseline": int((df["a_note"] == "BLOCKED_MAX_SWITCH_PER_DAY").sum()),
        "blocked_cap_boost": int((df["b_note"] == "BLOCKED_MAX_SWITCH_PER_DAY").sum()),
        "blocked_hold_baseline": int((df["a_note"] == "BLOCKED_MIN_HOLD").sum()),
        "blocked_hold_boost": int((df["b_note"] == "BLOCKED_MIN_HOLD").sum()),
    }

    # flip 샘플만 별도 표시
    flip_df = df[df["flip"] == 1].copy()
    cols = [
        "a_ts",
        "a_date","a_regime","a_z_score",
        "a_current_symbol_before","a_best_symbol",
        "a_diff_best_minus_current","a_gap_effective","a_switch","a_note",
        "b_gap_effective","b_switch","b_note",
        "a_margin","b_margin",
    ]
    flip_df = flip_df[cols] if not flip_df.empty else flip_df

    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    flip_df.to_csv(out, index=False, encoding="utf-8-sig")

    print("[SUMMARY]")
    for k,v in summary.items():
        print(f"{k}: {v}")
    print(f"[SAVED] {out.as_posix()}")

if __name__ == "__main__":
    main()
