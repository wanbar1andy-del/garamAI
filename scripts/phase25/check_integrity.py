
import pandas as pd
import numpy as np
from pathlib import Path

def check_integrity():
    tape_path = Path("results/phase24/tape/decision_tape.csv")
    flow_path = Path("results/phase25/analysis/005930_investor_flow_metrics.csv")
    
    print("[1] Loading Files...")
    if not tape_path.exists():
        print(f"FAIL: Tape not found {tape_path}")
        return
    if not flow_path.exists():
        print(f"FAIL: Flow not found {flow_path}")
        return
        
    tape = pd.read_csv(tape_path)
    flow = pd.read_csv(flow_path)
    
    # Date Normalize
    tape["date"] = pd.to_datetime(tape["date"])
    flow["date"] = pd.to_datetime(flow["date"])
    
    # 1. Overlap Check
    common_dates = pd.merge(tape[["date"]], flow[["date"]], on="date")
    n_common = len(common_dates)
    print(f"[2] Overlap Check: {n_common} days overlap.")
    if n_common == 0:
        print("CRITICAL FAIL: No overlapping dates found. Tuning impossible.")
        print(f"Tape Range: {tape['date'].min()} ~ {tape['date'].max()}")
        print(f"Flow Range: {flow['date'].min()} ~ {flow['date'].max()}")
        return

    # 2. Z-Score Quality
    print("[3] Z-Score Quality Check")
    z_cols = [c for c in flow.columns if "z20" in c]
    if not z_cols:
        print("FAIL: No Z-score columns found in flow metrics.")
        return
        
    for c in z_cols:
        s = flow[c]
        nan_ratio = s.isna().mean()
        std_val = s.std()
        print(f" - {c}: NaN={nan_ratio:.2%}, Std={std_val:.4f}")
        
        if std_val < 0.1:
            print(f"   WARNING: Signal {c} has very low variance (flat).")

    print("[4] Recommendation")
    # Recommended columns (Foreigner ratio / Pension ratio)
    recs = [c for c in z_cols if "ratio" in c and ("외국인" in c or "연기금" in c)]
    print(f"Recommended Features: {recs}")
    
    if n_common > 10:
        print("GATE PASSED: Proceed to Tuning.")
    else:
        print("GATE WARN: Low overlap count.")

if __name__ == "__main__":
    check_integrity()
