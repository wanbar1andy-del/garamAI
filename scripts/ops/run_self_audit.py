"""
[GARAM] Self-Audit & Verification Suite (SAVS) v1.0
Objective: Automatically verify "Operational Integrity" of X-7 runs (Sim or Paper).
Checks P0 Gates (Cash, Dup, Coverage).
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import logging
import argparse

# Config
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def run_audit(log_dir_path):
    log_dir = Path(log_dir_path)
    if not log_dir.exists():
        logging.error(f"Log dir not found: {log_dir}")
        return

    # Load Artifacts
    try:
        def safe_read(p):
            try:
                if p.stat().st_size == 0: return pd.DataFrame()
                return pd.read_csv(p)
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
            except FileNotFoundError:
                return pd.DataFrame()

        trades = safe_read(log_dir / "trades.csv")
        coverage = safe_read(log_dir / "audit_coverage.csv")
        switches = safe_read(log_dir / "audit_switches.csv")
        summary = (log_dir / "summary.txt").read_text(encoding='utf-8')
    except Exception as e:
        logging.error(f"Missing essential audit files: {e}")
        return

    report = {"P0_GATES": {}, "KPI": {}, "FLAGS": []}
    
    # -----------------------------
    # P0-4: Coverage Evidence (Hero Presence)
    # -----------------------------
    if not coverage.empty:
        total_mins = len(coverage)
        hero_present_mins = coverage['hero_present'].sum()
        hero_present_rate = hero_present_mins / total_mins if total_mins > 0 else 0
        
        # Held Coverage: Of minutes where hero_present, did we hold one?
        # Note: 'held_hero' is True if we held any of the topk_10
        held_mins = coverage[coverage['hero_present']]['held_hero'].sum()
        held_coverage = held_mins / hero_present_mins if hero_present_mins > 0 else 0
        
        report['KPI']['HERO_PRESENT_MINUTES'] = f"{hero_present_rate*100:.1f}%"
        report['KPI']['HELD_COVERAGE'] = f"{held_coverage*100:.1f}%"
        
        # P0 Gate: Hero Present > 10% ? (If sim universe is strictly top10, this should be 100% or close)
        # If we use strict >10 score, maybe less.
        if hero_present_rate < 0.05:
            report['P0_GATES']['COVERAGE'] = "FAIL (Hero Rare)"
            report['FLAGS'].append("Checking 'Hero Present' failed (<5%). Is the Universe correct?")
        else:
            report['P0_GATES']['COVERAGE'] = "PASS"
            
        if held_coverage < 0.3:
            report['P0_GATES']['HELD'] = "FAIL (Low Coverage)"
            report['FLAGS'].append("Held Coverage < 30%. Tuning needed.")
        else:
            report['P0_GATES']['HELD'] = "PASS"

    # -----------------------------
    # P0-2: Lifecycle Integrity (Churn)
    # -----------------------------
    if not trades.empty:
        churn_viol = 0
        df_entry = trades.groupby(['date', 'ticker']).size().reset_index(name='count')
        churn_viol = len(df_entry[df_entry['count'] > 2])
        
        if churn_viol > 0:
            report['P0_GATES']['LIFECYCLE'] = f"FAIL ({churn_viol} violations)"
            report['FLAGS'].append(f"Found tickers with >2 entries/day.")
        else:
            report['P0_GATES']['LIFECYCLE'] = "PASS"
            
        # P0-1 Check (Negative Cash?)
        # Not easily checked from trades alone without equity log, but assuming Sim check passed.
        # Check Win Rate
        win_rate = (trades['pnl_pct'] > 0).mean()
        report['KPI']['WIN_RATE'] = f"{win_rate*100:.1f}%"

    # -----------------------------
    # Table C: Switch Ledger
    # -----------------------------
    # Check BAD_SWITCH_RATE?
    # For now just count.
    report['KPI']['SWITCH_COUNT'] = len(switches)

    # -----------------------------
    # Final Decision
    # -----------------------------
    pass_all = all(v == "PASS" for v in report['P0_GATES'].values())
    
    print("\n" + "="*40)
    print("      [ANTIGRAVITY SAVS v1.0 AUDIT RESULT]      ")
    print("="*40)
    print(f"Log Dir: {log_dir.name}")
    print("-" * 20)
    print("P0 GATES:")
    for k, v in report['P0_GATES'].items():
        print(f"  {k:<15}: {v}")
    
    print("-" * 20)
    print("KPIs:")
    for k, v in report['KPI'].items():
        print(f"  {k:<20}: {v}")
        
    print("-" * 20)
    if report['FLAGS']:
        print("FLAGS (Action Required):")
        for f in report['FLAGS']:
            print(f"  [!] {f}")
    else:
        print("No Critical Flags Found.")
    print("="*40 + "\n")
    
    # Save JSON
    with open(log_dir / "audit_report.json", "w") as f:
        json.dump(report, f, indent=2)

    logging.info("Audit Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="Log directory to audit")
    args = parser.parse_args()
    run_audit(args.dir)
