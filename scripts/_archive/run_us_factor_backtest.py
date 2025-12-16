"""
CLI Script for US Factor Backtest
"""

import argparse
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.us_academic.us_factor_backtest import USFactorBacktestRunner

def main():
    parser = argparse.ArgumentParser(description="Run US Factor Backtest")
    parser.add_argument("--start", type=str, default="2015-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="End date YYYY-MM-DD")
    parser.add_argument("--strategies", type=str, default="US_MOM_12_1,US_VAL", help="Comma-separated strategy names")
    parser.add_argument("--cost_bp", type=float, default=20.0, help="Transaction cost in bps")
    
    args = parser.parse_args()
    
    runner = USFactorBacktestRunner()
    strategies = args.strategies.split(",")
    
    print(f"Starting US Factor Backtest from {args.start} to {args.end}")
    print(f"Strategies: {strategies}")
    print("-" * 50)
    
    for strategy in strategies:
        print(f"\nRunning {strategy}...")
        result = runner.run_backtest(strategy.strip(), args.start, args.end, args.cost_bp)
        
        status = "APPROVED" if result.approved else "REJECTED"
        print(f"Result: {status}")
        print(f"Metrics: Sharpe={result.metrics['sharpe']:.2f}, MaxDD={result.metrics['max_drawdown']:.2f}, CAGR={result.metrics['cagr']:.2f}")
        
        if not result.approved:
            print("Failed Criteria:")
            for failure in result.failed_criteria:
                print(f"  - {failure}")

if __name__ == "__main__":
    main()
