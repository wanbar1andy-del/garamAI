"""
Run Gap Analysis
Compares two backtest result pickles (Baseline vs Miracle) and generates a Gap Report.
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

from garam.research.regime.miracle_engine import TradeComparator, Trade

def load_result(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

def main():
    parser = argparse.ArgumentParser(description="Run Gap Analysis")
    parser.add_argument("--baseline", type=str, required=True, help="Path to Baseline pickle")
    parser.add_argument("--miracle", type=str, required=True, help="Path to Miracle pickle")
    parser.add_argument("--out_csv", type=str, default="gap_report.csv", help="Output CSV path")
    parser.add_argument("--out_summary", type=str, default="gap_summary.json", help="Output Summary JSON path")
    
    args = parser.parse_args()
    
    # 1. Load Results
    print(f"Loading Baseline: {args.baseline}")
    res_b = load_result(args.baseline)
    trades_b = res_b['trades']
    
    print(f"Loading Miracle: {args.miracle}")
    res_m = load_result(args.miracle)
    trades_m = res_m['trades']
    
    print(f"Baseline Trades: {len(trades_b)}")
    print(f"Miracle Trades: {len(trades_m)}")
    
    # 2. Run Comparison
    print("Running TradeComparator...")
    comparator = TradeComparator(trades_b, trades_m)
    df_gap = comparator.run_comparison()
    
    # 3. Calculate Summary Metrics
    matched = df_gap[df_gap['type'] == 'MATCHED']
    missed = df_gap[df_gap['type'] == 'MISSED_OPPORTUNITY']
    
    summary = {
        'total_baseline_trades': len(trades_b),
        'total_miracle_trades': len(trades_m),
        'matched_count': len(matched),
        'missed_count': len(missed),
        'missed_ratio': len(missed) / len(trades_m) if len(trades_m) > 0 else 0,
        'avg_entry_gap_days': matched['entry_gap_days'].mean() if not matched.empty else 0,
        'avg_pnl_gap': matched['pnl_gap'].mean() if not matched.empty else 0,
        'total_pnl_baseline': sum(t.pnl_pct for t in trades_b),
        'total_pnl_miracle': sum(t.pnl_pct for t in trades_m),
        'missed_pnl_sum': missed['miracle_pnl'].sum() if not missed.empty else 0
    }
    
    # 4. Save Outputs
    print(f"Saving Gap Report to {args.out_csv}...")
    df_gap.to_csv(args.out_csv, index=False)
    
    print(f"Saving Summary to {args.out_summary}...")
    with open(args.out_summary, 'w') as f:
        json.dump(summary, f, indent=4)
        
    print("\nSummary:")
    print(json.dumps(summary, indent=4))

if __name__ == "__main__":
    main()
