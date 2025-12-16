# scripts/run_param_conflict_report.py
# PARAM_CONFLICT_REPORT
# Aggregates debug logs to identify "Veto" blocks.

import pandas as pd
import numpy as np
from pathlib import Path
import glob

def load_debug_files(pattern="results/*_debug.csv"):
    files = glob.glob(pattern)
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["source_file"] = Path(f).name
            dfs.append(df)
        except Exception as e:
            print(f"Skipping {f}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def analyze_conflicts(df):
    if df.empty:
        print("No debug data found.")
        return

    print(">>> PARAMETER CONFLICT REPORT <<<")
    print(f"Total Bars Analyzed: {len(df)}")
    
    # 1. Block Rate (Signal Existed but Vetoed)
    # Entry Signal == True but Final Action != ENTER?
    # Actually, replay_runner logic: if vetoed, action might fail to be scheduled?
    # In my logic, I scheduled it but maybe blocked at execution time?
    # Wait, the logging logic I added captures 'veto_reason' IF action == BUY.
    # So if action == BUY and veto_reason is NOT None, that is a BLOCK.
    
    potential_entries = df[df["entry_signal"] == True]
    blocked_entries = potential_entries[potential_entries["veto_reason"].notna()]
    
    print("\n[1] BLOCK RATE BREAKDOWN")
    print(f"Potential Entry Signals: {len(potential_entries)}")
    print(f"Blocked Entries (Veto): {len(blocked_entries)}")
    if len(potential_entries) > 0:
        print(f"Block Rate: {len(blocked_entries)/len(potential_entries)*100:.2f}%")
    
    if not blocked_entries.empty:
        print("\nTop Veto Reasons:")
        print(blocked_entries["veto_reason"].value_counts())
    
    # 2. Regime Heatmap (Where do blocks happen?)
    print("\n[2] REGIME CONFLICT HEATMAP")
    if not blocked_entries.empty:
        heatmap = pd.crosstab(blocked_entries["regime"], blocked_entries["veto_reason"])
        print(heatmap)
    else:
        print("No blocks to map.")
        
    # 3. WAIT % KPI
    # Action == "HOLD" (or None) count
    wait_count = len(df[(df["action"].isin(["HOLD", None, np.nan])) & (df["pos"] == False)])
    wait_pct = wait_count / len(df) * 100
    
    print("\n[3] WAIT % KPI")
    print(f"Total Wait Bar: {wait_count}")
    print(f"Wait Ratio: {wait_pct:.2f}% (Target < 80% for Active, > 99% for Sniper)")

if __name__ == "__main__":
    df = load_debug_files("results/*_debug.csv")
    analyze_conflicts(df)
