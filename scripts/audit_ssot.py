import json
import argparse
from pathlib import Path
import sys

def audit_ssot(ssot_pointer_path):
    print(f"[AUDIT] Checking SSOT Pointer: {ssot_pointer_path}")
    
    try:
        with open(ssot_pointer_path, "r") as f:
            ssot = json.load(f)
    except FileNotFoundError:
        print("[FAIL] SSOT Pointer file not found.")
        sys.exit(1)
        
    latest_run = ssot.get("latest_run", {})
    run_path = Path(latest_run.get("path", ""))
    metrics_path = Path(latest_run.get("metrics_file", ""))
    
    if not run_path.exists():
        print(f"[FAIL] Run directory missing: {run_path}")
        sys.exit(1)
        
    if not metrics_path.exists():
        print(f"[FAIL] Metrics file missing: {metrics_path}")
        sys.exit(1)
        
    # Load Metrics
    with open(metrics_path, "r") as f:
        metrics = json.load(f)
        
    # Load Manifest
    manifest_path = run_path / "manifest.json"
    if not manifest_path.exists():
        print(f"[FAIL] Manifest missing: {manifest_path}")
        sys.exit(1)
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    # Load Benchmarks
    bench_path = run_path.parent / f"benchmarks_{manifest['end_date'].replace('-','')}.json"
    # Or just look for any benchmark file in the run dir if calculated?
    # Usually benchmarks.json or similar.
    # The previous step generated results/replay/benchmarks_20251219.json covering the period.
    # But usually benchmarks should be inside the run folder or linked.
    # For now, we check the latest benchmark run if available.
    
    # 1. Invariants Check
    failures = []
    
    # Return
    expected_ret = latest_run.get("return_pct")
    actual_ret = metrics.get("total_return_pct")
    if abs(expected_ret - actual_ret) > 0.05:
        failures.append(f"Return Mismatch: Expected {expected_ret}, Actual {actual_ret}")
        
    # Trades
    # n_trades isn't explicitly in SSOT_LATEST.json but is in checklist.
    # Let's check manifest trades vs metrics? Metrics doesn't have trade count usually.
    # Manifest has total_trades.
    total_trades = manifest.get("total_trades")
    # We might add expected_trades to SSOT_LATEST.json for strictness.
    if total_trades != 253:
        # Hardcoded for this specific Sealed Version
        failures.append(f"Trade Count Mismatch: Expected 253, Actual {total_trades}")
        
    # Cost
    if manifest.get("cost_semantics") != "roundtrip_total_bps":
        failures.append("Cost Semantics Mismatch")
        
    # Exit Strategy
    if manifest.get("exit_strategy") != "HOLD_1D":
        failures.append("Exit Strategy Mismatch")

    # 2. Benchmark Guardrail
    # We need benchmark values.
    # If benchmarks checks are required, we need to load them.
    # Assuming benchmarks_20251219.json exists
    bench_file = Path("results/replay/benchmarks_20251219.json")
    if bench_file.exists():
        with open(bench_file, "r") as f:
            bench = json.load(f)
            univ_ret = bench["metrics"]["Universe_EW"]["return_pct"]
            if actual_ret < univ_ret:
                failures.append(f"Benchmark Guardrail: Engine ({actual_ret:.2f}%) < Universe ({univ_ret:.2f}%)")
            
            # Bull Market Check
            samsung = bench["metrics"].get("Single_Name_005930")
            if samsung:
                samsung_ret = samsung["return_pct"]
                if samsung_ret > 0 and actual_ret < samsung_ret:
                     # This is a Warning in general, but Failure if strict Bull Market rule applied?
                     # User said "Bull Market Rule: If Engine < Single Anchor, investigate".
                     # Let's mark it as WARN.
                     print(f"[WARN] Engine ({actual_ret:.2f}%) < Samsung ({samsung_ret:.2f}%)? (Check Friction)")
    
    if failures:
        print("[FAIL] Audit Failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
        
    print("[PASS] SSOT Integrity Verified.")
    print(f"  Return: {actual_ret:.2f}% (Expected {expected_ret:.2f}%)")
    print(f"  Trades: {total_trades}")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssot", default="docs/ssot/SSOT_LATEST.json")
    args = parser.parse_args()
    
    audit_ssot(args.ssot)
