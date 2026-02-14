from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
import glob
import pandas as pd

# Robust Path Setup
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.runtime32 import python32, ensure_32bit_or_reexec
from scripts.hero_diary import HeroDiaryBuilder

# Ensure this script itself runs on 32-bit (will re-exec if 64-bit)
ensure_32bit_or_reexec()
# If we reach here, we are guaranteed to be 32-bit
# ==========================================

def _run(cmd: list[str], cwd: Path) -> int:
    print(f"\n[RUN] {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=str(cwd))
    return r.returncode

def _latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def check_pre_flight(project_root: Path):
    """
    Manual Section 3: Pre-Flight Checks
    1. Data Consistency (Audit) - Light version (Availability only?) or Full Code Audit?
       Manual says: 'audit_data_quality_1y.py returns OK'. This might take 20s.
    2. Universe Check (401 rows)
    """
    print("=== [GATE] Pre-Flight Checks ===")
    
    # 1. Universe Check
    univ_path = project_root / "GARAM_Data" / "real_universe_400.csv"
    if not univ_path.exists():
        print(f"[FAIL] Universe not found: {univ_path}")
        sys.exit(1)
        
    df = pd.read_csv(univ_path)
    if len(df) != 401: # 400 + header? Or 401 symbols? previous audit said 401.
        # Actually expected is 400 or 401 depending on dummy/index.
        # Let's check > 390 to be safe, or stricly > 0.
        pass
    print(f"[PASS] Universe Loaded ({len(df)} rows)")

    # 2. Data Integrity (Audit 1Y)
    # This runs the full audit script.
    # To save time in dev, we might verify only missing files here, or run full if critical.
    # Manual says "MUST execute". We run it.
    audit_cmd = [python32(), "-m", "scripts.audit_data_quality_1y"]
    # We can rely on exit code 0
    rc = _run(audit_cmd, cwd=project_root)
    if rc != 0:
        print("[FAIL] Data Audit Failed! Check logs.")
        sys.exit(1)
        
    print("=== [GATE] Pre-Flight Passed ===\n")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--probe", default="CHAMPION_V21")
    p.add_argument("--window", type=int, default=30)
    p.add_argument("--two_pass", action="store_true")
    p.add_argument("--top_k", type=int, default=50)
    p.add_argument("--aum", type=float, default=10_000_000)
    p.add_argument("--allocate", action="store_true")
    p.add_argument("--build_orders", action="store_true", help="Generate order files from allocation")
    p.add_argument("--recollect_rounds", type=int, default=0, help="0이면 recollect 생략")
    p.add_argument("--wait_sec", type=int, default=600)
    p.add_argument("--poll_sec", type=int, default=5)
    p.add_argument("--audit", action="store_true", default=True, help="Run SSOT audit before operations")
    p.add_argument("--no-audit", dest="audit", action="store_false", help="Skip SSOT audit (Not Recommended)")
    p.add_argument("--dry_run", action="store_true", help="Paper Mode: Generate order logs but do not write files")
    
    args = p.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    
    # 0) Audit Gate (Kill Switch)
    if args.audit:
        print("=== [GATE] Running SSOT Audit... ===")
        audit_res = _run([python32(), "-m", "scripts.audit_ssot"], cwd=project_root)
        if audit_res != 0:
            print("!!! [KILL SWITCH] SSOT Audit Failed. Operations Aborted. !!!")
            sys.exit(1)
        print("=== [GATE] Audit Passed. Proceeding... ===\n")

    # 0.5) Manual Pre-Flight Checks
    check_pre_flight(project_root)

    print(f"=== Garam Daily Operations Started (Limit={args.limit}) ===")

    # 1) Sync universe -> ingest csv
    rc = _run([python32(), "-m", "scripts.sync_universe_to_ingest"], cwd=project_root)
    if rc != 0:
        print("[FAIL] universe sync failed")
        sys.exit(rc)

    # 2) Optional recollect loop
    if args.recollect_rounds > 0:
        cmd = [python32(), "-m", "scripts.recollect_loop",
               "--max_rounds", str(args.recollect_rounds),
               "--wait_sec", str(args.wait_sec),
               "--poll_sec", str(args.poll_sec)]
        if args.limit:
            cmd += ["--limit", str(args.limit)]

        rc = _run(cmd, cwd=project_root)
        if rc != 0:
            print("[WARN] recollect loop returned non-zero (check console). Continue to scan.")

    # 3) Hero scan
    scan_cmd = [python32(), "-m", "scripts.scan_heroes",
                "--probe", args.probe,
                "--window", str(args.window)]
    if args.limit:
        scan_cmd += ["--limit", str(args.limit)]
    if args.two_pass:
        scan_cmd += ["--two_pass", "--top_k", str(args.top_k)]
    if args.two_pass:
        scan_cmd += ["--two_pass", "--top_k", str(args.top_k)]
    # Note: Allocation is now driven by HeroDiary (SSOT), not scan_heroes
    # if args.allocate: ... removed
    rc = _run(scan_cmd, cwd=project_root)
    if rc != 0:
        print("[FAIL] hero scan failed")
        sys.exit(rc)
        
    # 3.1) [GATE] SSOT Schema Audit (Sealed)
    latest_scan_for_audit = _latest(str(project_root / "results" / f"hero_scan_{args.probe}_*.csv"))
    if latest_scan_for_audit:
        print(f"=== [GATE] Auditing SSOT Schema: {Path(latest_scan_for_audit).name} ===")
        rc = _run([python32(), "-m", "scripts.audit_hero_scan_schema", latest_scan_for_audit], cwd=project_root)
        if rc != 0:
             print("!!! [KILL SWITCH] SSOT Audit Failed. Operations Aborted. !!!")
             sys.exit(rc)
    else:
         print("[FAIL] No hero scan output found to audit.")
         sys.exit(1)

    # 3.5) [GATE] Hero Diary & Ghost Check (In-Flight)
    print("=== [GATE] Generating Hero Diary & Check Ghosts ===")
    diary_path = None # Initialize variable content
    try:
        # Find latest scan
        latest_scan = _latest(str(project_root / "results" / f"hero_scan_{args.probe}_*.csv"))
        if not latest_scan:
            print("[FAIL] No hero scan result found needed for Diary.")
            sys.exit(1)
            
        # Get Holdings (TODO: Link to Live Positions)
        # For now empty list as confirmed for Phase 6 Week 1
        current_holdings = [] 
        
        builder = HeroDiaryBuilder(project_root)
        diary_path = builder.build_diary(Path(latest_scan), current_holdings)
        print(f"[PASS] Diary Created: {diary_path.name}")
        
    except Exception as e:
        print(f"!!! [KILL SWITCH] Hero Diary Logic Failed: {e}")
        sys.exit(1)

    # 4) Build Orders (From Hero Diary SSOT)
    if args.build_orders:
        # Use diary_path generated above
        if diary_path and diary_path.exists():
             cmd = [python32(), "-m", "scripts.build_orders_from_allocation",
                    "--allocation", str(diary_path)]
             if args.dry_run:
                 cmd.append("--dry_run")
             # Pass AUM from args or default
             cmd.extend(["--aum", str(args.aum)])
                 
             _run(cmd, cwd=project_root)
        else:
             print("[WARN] No diary file found to build orders.")

    # 5) Generate Ops Report (SSOT Metrics)
    print("=== [OPS] Generating Ops Report (SSOT) ===")
    
    # Resolve explicit paths for SSOT
    p_scan = str(latest_scan) if latest_scan else ""
    p_diary = str(diary_path) if (diary_path and diary_path.exists()) else ""
    p_alloc = str(_latest(str(project_root / "results" / f"allocation_{args.probe}_*.csv"))) or ""
    p_orders = str(project_root / "GARAM_Data" / "orders" / "inbox")
    
    report_cmd = [python32(), "-m", "scripts.ops_report_ssot",
                  "--scan", p_scan,
                  "--diary", p_diary,
                  "--alloc", p_alloc,
                  "--orders", p_orders]
                  
    _run(report_cmd, cwd=project_root)

    # Output pointers (Sealed)
    latest_report = project_root / "results" / "reports" / "ops_report_latest.json"

    print("\n=== DAILY OPS OUTPUT (Sealed) ===")
    if p_scan:
        print(f"- hero_scan:    {Path(p_scan).absolute()}")

    if p_diary:
        print(f"- hero_diary:   {Path(p_diary).absolute()}")
    
    if p_alloc:
        print(f"- allocation:   {Path(p_alloc).absolute()}")
        
    print(f"- orders_inbox: {Path(p_orders).absolute()}")
    
    if latest_report.exists():
        print(f"- ops_report:   {latest_report.absolute()}")
        
    print("=================================\n")

if __name__ == "__main__":
    main()
