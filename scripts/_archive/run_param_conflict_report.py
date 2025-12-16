"""
Run Parameter Conflict Report
Analyzes signal logs (pickle/parquet) to identify why valid signals are not executed.
Generates a JSON report detailing block rates and top rejection reasons.
"""

import pandas as pd
import pickle
import argparse
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

def analyze_logs(logs):
    if not logs:
        return {}
        
    df = pd.DataFrame(logs)
    
    # Filter for raw signals only
    df_signals = df[df['signal_raw'] == True].copy()
    total_signals = len(df_signals)
    
    if total_signals == 0:
        return {'total_signals': 0}
        
    executed_count = df_signals['executed'].sum()
    executed_ratio = executed_count / total_signals
    
    # Block Counts
    block_counts = df_signals['block_source'].value_counts().to_dict()
    
    # Reason Counts
    filter_reasons = df_signals['filter_reason'].value_counts().to_dict()
    risk_reasons = df_signals['risk_reason'].value_counts().to_dict()
    
    # Regime Breakdown
    # Assuming 'regime' might be in the log or we need to join with data.
    # For now, we'll stick to global stats as the logs in miracle_engine.py 
    # don't explicitly store regime in the log dict yet (we should add it).
    
    return {
        'total_signals': int(total_signals),
        'executed_count': int(executed_count),
        'executed_ratio': float(executed_ratio),
        'block_counts': block_counts,
        'filter_reasons': filter_reasons,
        'risk_reasons': risk_reasons
    }

def main():
    parser = argparse.ArgumentParser(description="Run Parameter Conflict Report")
    parser.add_argument("--backtest_result", type=str, required=True, help="Path to backtest result pickle (containing signal_logs)")
    parser.add_argument("--out", type=str, default="param_conflict_report.json", help="Output JSON path")
    
    args = parser.parse_args()
    
    print(f"Loading backtest result: {args.backtest_result}")
    with open(args.backtest_result, 'rb') as f:
        res = pickle.load(f)
        
    # Check if signal_logs exists in result
    # We need to update run_policy_backtest.py to save this!
    # For now, let's assume it's there or we need to re-run backtest.
    
    if 'signal_logs' not in res:
        print("Error: 'signal_logs' not found in backtest result.")
        print("Please re-run run_policy_backtest.py with the updated engine.")
        return

    logs = res['signal_logs']
    print(f"Analyzing {len(logs)} logs...")
    
    report = analyze_logs(logs)
    
    print(f"Saving report to {args.out}...")
    with open(args.out, 'w') as f:
        json.dump(report, f, indent=4)
        
    print("\nConflict Report Summary:")
    print(json.dumps(report, indent=4))

if __name__ == "__main__":
    main()
