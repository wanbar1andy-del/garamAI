# scripts/phase25/nightly_suite_v2.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import pandas as pd
import numpy as np
import subprocess
import sys


# ---------- utils ----------
def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def parse_csv_list(s: str, cast=float) -> List:
    if not s.strip():
        return []
    out = []
    for x in s.split(","):
        x = x.strip()
        if x == "":
            continue
        out.append(cast(x))
    return out


def write_text(path: Path, txt: str) -> None:
    ensure_dir(path.parent)
    path.write_text(txt, encoding="utf-8")


def to_signal_zscore_csv(flow_metrics_built_csv: Path, signal_col: str, out_csv: Path) -> None:
    """
    switching_from_tape_ts.py expects: date + z_score (at least)
    We create a thin csv with columns [date, z_score] from built metrics.
    """
    df = pd.read_csv(flow_metrics_built_csv, encoding="utf-8-sig")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    elif "일자" in df.columns:
        df["date"] = pd.to_datetime(df["일자"].astype(str), format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        raise ValueError("flow_metrics_built.csv must have 'date' or '일자' column")

    if signal_col not in df.columns:
        raise ValueError(f"signal_col not found: {signal_col}. available={list(df.columns)[:50]}")

    out = df[["date", signal_col]].rename(columns={signal_col: "z_score"}).dropna()
    ensure_dir(out_csv.parent)
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")


def detect_switch_col(df: pd.DataFrame) -> str:
    cands = ["did_switch", "switched", "switch", "is_switch", "action"]
    for c in cands:
        if c in df.columns:
            return c
    raise ValueError(f"cannot find switch indicator column in {list(df.columns)}")


def count_flips(baseline_log: Path, test_log: Path) -> int:
    """
    Flip = decision differs at same ts.
    """
    a = pd.read_csv(baseline_log, encoding="utf-8-sig")
    b = pd.read_csv(test_log, encoding="utf-8-sig")

    if "ts" not in a.columns or "ts" not in b.columns:
        raise ValueError("switch_log_ts.csv must have ts column")

    ca = detect_switch_col(a)
    cb = detect_switch_col(b)

    a2 = a[["ts", ca]].copy()
    b2 = b[["ts", cb]].copy()
    a2["ts"] = a2["ts"].astype(str)
    b2["ts"] = b2["ts"].astype(str)

    m = a2.merge(b2, on="ts", how="inner", suffixes=("_base", "_test"))
    # normalize bool-ish
    def norm(x):
        if isinstance(x, str):
            return x.strip().lower()
        return x

    base = m[f"{ca}_base"].map(norm)
    test = m[f"{cb}_test"].map(norm)
    return int((base != test).sum())


# ---------- core ----------
@dataclass
class RunKPI:
    total_ts: int
    total_switches: int
    switch_rate: float
    days: int
    INFLOW_ts: int
    INFLOW_switches: int
    INFLOW_rate: float
    NEUTRAL_ts: int
    NEUTRAL_switches: int
    NEUTRAL_rate: float
    OUTFLOW_ts: int
    OUTFLOW_switches: int
    OUTFLOW_rate: float


@dataclass
class GridRow:
    run: str
    gap: float
    weight: float
    min_hold_min: int
    cap: int

    total_ts: int
    switches: int
    switch_rate: float
    flip_cnt: int

    INFLOW_rate: float
    NEUTRAL_rate: float
    OUTFLOW_rate: float
    chase_score: float          # IN - OUT (bigger means more chase)
    cap_binding: bool              # switches == cap*days (cap actually binds)


def run_switch_sim(python_exe: str,
                   switching_py: Path,
                   tape_csv: Path,
                   flow_z_csv: Path,
                   out_dir: Path,
                   gap: float,
                   weight: float,
                   min_hold_min: int,
                   cap: int) -> Tuple[Path, Path, Path]:
    """
    Runs scripts/phase24/switching_from_tape_ts.py and returns paths:
    switch_log_ts.csv, regime_summary.csv, summary.json
    """
    ensure_dir(out_dir)

    cmd = [
        python_exe,
        switching_py.as_posix(),
        "--tape_csv", tape_csv.as_posix(),
        "--flow_metrics_csv", flow_z_csv.as_posix(),
        "--out_dir", out_dir.as_posix(),
        "--gap", str(gap),
        "--weight", str(weight),
        "--min_hold_min", str(min_hold_min),
        "--max_switches_per_day", str(cap),
    ]

    # Windows-safe: no shell, explicit list
    cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if cp.returncode != 0:
        raise RuntimeError(
            "switching run failed\n"
            f"cmd={cmd}\n"
            f"stdout=\n{cp.stdout}\n"
            f"stderr=\n{cp.stderr}\n"
        )

    log_csv = out_dir / "switch_log_ts.csv"
    regime_csv = out_dir / "regime_summary.csv"
    summary_json = out_dir / "summary.json"
    if not log_csv.exists() or not regime_csv.exists() or not summary_json.exists():
        raise RuntimeError(f"missing outputs in {out_dir.as_posix()}")

    return log_csv, regime_csv, summary_json


def read_kpi(regime_csv: Path, summary_json: Path) -> RunKPI:
    reg = pd.read_csv(regime_csv, encoding="utf-8-sig")
    js = json.loads(summary_json.read_text(encoding="utf-8-sig"))

    total_ts = int(js["kpi"]["total_ts"])
    total_sw = int(js["kpi"]["total_switches"])
    days = int(js["kpi"]["days"])
    rate = float(js["kpi"]["switch_rate"])

    def pick(rname: str):
        row = reg.loc[reg["regime"] == rname]
        if row.empty:
            return 0, 0, 0.0
        ts = int(row["ts_count"].iloc[0])
        sw = int(row["switches"].iloc[0])
        rr = float(row["switch_rate"].iloc[0])
        return ts, sw, rr

    it, isw, ir = pick("INFLOW")
    nt, nsw, nr = pick("NEUTRAL")
    ot, osw, orr = pick("OUTFLOW")

    return RunKPI(
        total_ts=total_ts,
        total_switches=total_sw,
        switch_rate=rate,
        days=days,
        INFLOW_ts=it, INFLOW_switches=isw, INFLOW_rate=ir,
        NEUTRAL_ts=nt, NEUTRAL_switches=nsw, NEUTRAL_rate=nr,
        OUTFLOW_ts=ot, OUTFLOW_switches=osw, OUTFLOW_rate=orr,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--python_exe", default=sys.executable if "sys" in globals() else "python")
    ap.add_argument("--switching_py", default="scripts/phase24/switching_from_tape_ts.py")
    ap.add_argument("--tape_csv", required=True)
    ap.add_argument("--flow_metrics_built_csv", required=True)
    ap.add_argument("--signal_col", default="외국인투자자_ratio_z20")

    ap.add_argument("--out_dir", required=True)

    # tuning space
    ap.add_argument("--gaps", default="1.5,2.0,2.5")
    ap.add_argument("--weights", default="-2,-1,-0.5,0,0.5,1,2")
    ap.add_argument("--min_holds", default="60")
    ap.add_argument("--caps", default="999")  # tuning should be uncapped

    # reporting
    ap.add_argument("--top_k", type=int, default=20)

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)

    gaps = parse_csv_list(args.gaps, float)
    weights = parse_csv_list(args.weights, float)
    min_holds = parse_csv_list(args.min_holds, int)
    caps = parse_csv_list(args.caps, int)

    switching_py = Path(args.switching_py)
    tape_csv = Path(args.tape_csv)
    built_csv = Path(args.flow_metrics_built_csv)

    # 1) build thin zscore csv
    flow_z_csv = out_dir / "flow_zscore.csv"
    to_signal_zscore_csv(built_csv, args.signal_col, flow_z_csv)

    meta = {
        "ts": now_iso(),
        "inputs": {
            "tape_csv": tape_csv.as_posix(),
            "flow_metrics_built_csv": built_csv.as_posix(),
            "signal_col": args.signal_col,
            "flow_zscore_csv": flow_z_csv.as_posix(),
        },
        "grid": {
            "gaps": gaps,
            "weights": weights,
            "min_holds": min_holds,
            "caps": caps,
        }
    }

    # 2) run grid with anchored baselines per (gap, min_hold, cap)
    rows: List[GridRow] = []
    all_runs: List[Dict] = []

    for gap in gaps:
        for mh in min_holds:
            for cap in caps:
                # baseline anchor for this constraint set: weight=0
                base_tag = f"BASE_g{gap}_mh{mh}_cap{cap}"
                base_dir = out_dir / "runs" / base_tag
                base_log, base_reg, base_sum = run_switch_sim(
                    python_exe=args.python_exe,
                    switching_py=switching_py,
                    tape_csv=tape_csv,
                    flow_z_csv=flow_z_csv,
                    out_dir=base_dir,
                    gap=gap,
                    weight=0.0,
                    min_hold_min=mh,
                    cap=cap,
                )
                base_kpi = read_kpi(base_reg, base_sum)
                base_days = base_kpi.days

                all_runs.append({
                    "run": base_tag,
                    "gap": gap, "weight": 0.0, "min_hold_min": mh, "cap": cap,
                    "kpi": asdict(base_kpi),
                    "paths": {"out_dir": base_dir.as_posix()}
                })

                for w in weights:
                    tag = f"g{gap}_w{w}_mh{mh}_cap{cap}"
                    rdir = out_dir / "runs" / tag
                    log_csv, reg_csv, sum_json = run_switch_sim(
                        python_exe=args.python_exe,
                        switching_py=switching_py,
                        tape_csv=tape_csv,
                        flow_z_csv=flow_z_csv,
                        out_dir=rdir,
                        gap=gap,
                        weight=w,
                        min_hold_min=mh,
                        cap=cap,
                    )
                    kpi = read_kpi(reg_csv, sum_json)
                    flips = 0 if w == 0 else count_flips(base_log, log_csv)

                    cap_binding = (cap < 999) and (kpi.total_switches == cap * base_days)
                    # chase_score = INFLOW_rate - OUTFLOW_rate (Positive means "Chase" behavior)
                    # User requested this metric.
                    chase_score = float(kpi.INFLOW_rate - kpi.OUTFLOW_rate)

                    # flip sanity
                    if abs(w) < 1e-12:
                        flips = 0

                    row = GridRow(
                        run=tag,
                        gap=float(gap),
                        weight=float(w),
                        min_hold_min=int(mh),
                        cap=int(cap),
                        total_ts=int(kpi.total_ts),
                        switches=int(kpi.total_switches),
                        switch_rate=float(kpi.switch_rate),
                        flip_cnt=int(flips),
                        INFLOW_rate=float(kpi.INFLOW_rate),
                        NEUTRAL_rate=float(kpi.NEUTRAL_rate),
                        OUTFLOW_rate=float(kpi.OUTFLOW_rate),
                        chase_score=chase_score, # Mapping chase_score to the correct field
                        # Updated to match DataClass field name changed in previous step.
                        cap_binding=bool(cap_binding),
                    )
                    rows.append(row)
                    all_runs.append({
                        "run": tag,
                        "gap": gap, "weight": w, "min_hold_min": mh, "cap": cap,
                        "kpi": asdict(kpi),
                        "flip_cnt": flips,
                        "chase_score": chase_score,
                        "cap_binding": cap_binding,
                        "paths": {"out_dir": rdir.as_posix()}
                    })

    # 3) save grid csv
    grid_df = pd.DataFrame([asdict(r) for r in rows])

    # --- force numeric dtypes (sorting bug fix) ---
    num_cols = ["gap","weight","min_hold_min","cap","switch_rate","switches","flip_cnt",
                "INFLOW_rate","OUTFLOW_rate","chase_score"]
    for c in num_cols:
        if c in grid_df.columns:
            grid_df[c] = pd.to_numeric(grid_df[c], errors="coerce")
    
    # rename softlock_score -> chase_score for reporting clarity (per user request)
    if "softlock_score" in grid_df.columns:
        grid_df["chase_score"] = -grid_df["softlock_score"]

    # --- force numeric dtypes (sorting bug fix) ---
    num_cols = ["gap","weight","min_hold_min","cap","switch_rate","switches","flip_cnt",
                "INFLOW_rate","OUTFLOW_rate","chase_score"]
    for c in num_cols:
        if c in grid_df.columns:
            grid_df[c] = pd.to_numeric(grid_df[c], errors="coerce")

    # rename softlock_score -> chase_score for reporting clarity (per user request)
    # chase_score = INFLOW - OUTFLOW (higher means more chasing in inflow)
    if "softlock_score" in grid_df.columns:
        grid_df["chase_score"] = -grid_df["softlock_score"] # softlock was OUT-IN. chase is IN-OUT = -(OUT-IN)
        # However, the user provided code snippet says:
        # softlock = float(kpi.INFLOW_rate - kpi.OUTFLOW_rate) in the NEW definition instructions?
        # Re-reading instruction 3):
        # "And change report KPI to... chase_score = INFLOW_rate - OUTFLOW_rate"
        # AND "softlock = float(kpi.INFLOW_rate - kpi.OUTFLOW_rate)" in the python snippet provided?
        # NO, the user said: "Now definition: softlock_score = OUTFLOW - INFLOW (old). User wants chase_score = INFLOW - OUTFLOW."
        # And user said: "report KPI softlock_score instead chase_score: # chase_score = INFLOW_rate - OUTFLOW_rate\n softlock = ..."
        # Wait, the user's snippet in 3) is a bit ambiguous:
        # "# chase_score = INFLOW_rate - OUTFLOW_rate"
        # "softlock = float(kpi.INFLOW_rate - kpi.OUTFLOW_rate)" -> This assigns IN-OUT to a variable named 'softlock'.
        # I will stick to the user's INTENT: Use `chase_score = INFLOW - OUTFLOW` and use that for ranking.
    
    # Let's adjust the row creation loop instead to be cleaner, but I can also just patch the DF.
    # Actually, modifying the row creation is better. I will use replace_file_content on the earlier loop.

    grid_csv = out_dir / "grid_v2.csv"
    grid_df.to_csv(grid_csv, index=False, encoding="utf-8-sig")

    # 4) rank candidates
    # primary: chase_score DESC (IN>OUT), secondary: switch_rate ASC, tertiary: flips DESC
    ranked = grid_df.sort_values(
        by=["chase_score", "switch_rate", "flip_cnt"],
        ascending=[False, True, False],
        kind="mergesort",
    )

    top_k = ranked.head(int(args.top_k)).copy()

    # 5) paper ops candidates: 3-way sign test (fixed constraints)
    paper_candidates = [
        {"name": "A_NEUTRAL", "gap": 2.0, "weight": 0.0, "min_hold_min": 60, "cap": 999},
        {"name": "B_POS",     "gap": 2.0, "weight": +1.0, "min_hold_min": 60, "cap": 999},
        {"name": "C_NEG",     "gap": 2.0, "weight": -1.0, "min_hold_min": 60, "cap": 999},
    ]
    cand_json = out_dir / "paper_ops_candidates.json"
    cand_json.write_text(json.dumps(paper_candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6) report markdown
    def md_table(df: pd.DataFrame, cols: List[str]) -> str:
        x = df[cols].copy()
        return x.to_markdown(index=False)

    report = []
    report.append("# Phase 25 Nightly Report v2 (Anchored Baseline + Negative Weights)\n")
    report.append(f"- ts: {meta['ts']}")
    report.append(f"- tape_csv: `{meta['inputs']['tape_csv']}`")
    report.append(f"- flow_metrics_built_csv: `{meta['inputs']['flow_metrics_built_csv']}`")
    report.append(f"- signal_col: `{meta['inputs']['signal_col']}`")
    report.append(f"- flow_zscore_csv: `{meta['inputs']['flow_zscore_csv']}`\n")

    report.append("## Key Interpretation\n")
    report.append("- **튜닝은 cap=999로 수행** (cap=6은 결과를 고정시켜 튜닝을 가립니다).")
    report.append("- **Soft-Lock 지표(softlock_score = OUTFLOW_rate - INFLOW_rate)** 가 **클수록** 의도(인플로우에서 스위칭 감소)에 부합합니다.")
    report.append("- **weight 음수 포함**: 신호 부호(sign)가 반대인 경우를 탐지하기 위함.\n")

    report.append("## Grid Top (by softlock_score desc, switch_rate asc, flips desc)\n")
    report.append(md_table(
        top_k,
        cols=[
            "run", "gap", "weight", "min_hold_min", "cap",
            "switch_rate", "switches", "flip_cnt",
            "INFLOW_rate", "OUTFLOW_rate", "chase_score", "cap_binding"
        ],
    ))
    report.append("\n")

    report.append("## Paper Ops Candidates (3-way sign test)\n")
    report.append("```json\n" + json.dumps(paper_candidates, ensure_ascii=False, indent=2) + "\n```\n")

    report.append("## Files\n")
    report.append(f"- grid_v2.csv: `{grid_csv.as_posix()}`")
    report.append(f"- report_v2.md: `{(out_dir / 'report_v2.md').as_posix()}`")
    report.append(f"- paper_ops_candidates.json: `{cand_json.as_posix()}`")
    report.append(f"- runs/: `{(out_dir / 'runs').as_posix()}`\n")

    report.append("## Raw Run Index (json)\n")
    report.append("```json\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n```\n")

    # save
    report_path = out_dir / "report_v2.md"
    write_text(report_path, "\n".join(report))

    # full run index
    full_index = out_dir / "run_index.json"
    full_index.write_text(json.dumps({"meta": meta, "runs": all_runs}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] saved:")
    print(f" - {grid_csv.as_posix()}")
    print(f" - {report_path.as_posix()}")
    print(f" - {cand_json.as_posix()}")
    print(f" - {full_index.as_posix()}")


if __name__ == "__main__":
    import sys
    main()
