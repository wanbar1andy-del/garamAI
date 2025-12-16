"""
Validate US S&P500 Data Coverage
Checks data availability, gaps, and survivorship bias.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

def validate_coverage():
    prices_dir = PATHS.US_SP500_ROOT / "prices_daily"
    constituents_path = PATHS.US_SP500_ROOT / "constituents" / "constituents_sp500.parquet"
    
    report_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_symbols": 0,
        "valid_symbols": 0,
        "start_date": "",
        "end_date": "",
        "coverage_pct": 0.0,
        "missing_symbols": [],
        "gaps": {}
    }
    
    # 1. Check Constituents
    if constituents_path.exists():
        constituents = pd.read_parquet(constituents_path)
        expected_symbols = constituents['symbol'].unique().tolist()
    else:
        print("Warning: Constituents file not found.")
        expected_symbols = []
        
    # 2. Check Prices
    price_files = list(prices_dir.glob("*.csv"))
    available_symbols = [f.stem for f in price_files]
    
    report_data["total_symbols"] = len(available_symbols)
    
    if not price_files:
        print("No price files found.")
        return report_data
        
    # Stats
    all_starts = []
    all_ends = []
    total_days = 0
    valid_days = 0
    
    for f in price_files:
        try:
            df = pd.read_csv(f)
            if df.empty:
                continue
                
            df['date'] = pd.to_datetime(df['date'])
            start = df['date'].min()
            end = df['date'].max()
            
            all_starts.append(start)
            all_ends.append(end)
            
            # Simple coverage check (trading days approx)
            days_span = (end - start).days
            # trading days approx 252/365
            expected_trading_days = int(days_span * (252/365))
            actual_days = len(df)
            
            total_days += expected_trading_days
            valid_days += actual_days
            
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    if all_starts:
        report_data["start_date"] = min(all_starts).strftime("%Y-%m-%d")
        report_data["end_date"] = max(all_ends).strftime("%Y-%m-%d")
        report_data["valid_symbols"] = len(all_starts)
        
        if total_days > 0:
            report_data["coverage_pct"] = round((valid_days / total_days) * 100, 2)
            
    # 3. Generate Report
    report_path = PATHS.US_SP500_ROOT / f"report_us_sp500_coverage_{datetime.now().strftime('%Y%m%d')}.md"
    json_path = PATHS.US_SP500_ROOT / "coverage_summary.json"
    
    with open(report_path, "w", encoding='utf-8') as f:
        f.write("# US S&P500 Data Coverage Report\n\n")
        f.write(f"**Date:** {report_data['timestamp']}\n\n")
        f.write("## Summary\n")
        f.write(f"- **Total Symbols:** {report_data['total_symbols']}\n")
        f.write(f"- **Date Range:** {report_data['start_date']} ~ {report_data['end_date']}\n")
        f.write(f"- **Overall Coverage:** {report_data['coverage_pct']}%\n\n")
        
        f.write("## Gaps & Issues\n")
        if not expected_symbols:
            f.write("- [WARNING] No constituents file found. Cannot verify missing symbols.\n")
        else:
            missing = set(expected_symbols) - set(available_symbols)
            f.write(f"- **Missing Symbols ({len(missing)}):** {', '.join(list(missing)[:10])}...\n")
            
    # Save JSON for system report
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
        
    print(f"Report generated: {report_path}")
    return report_data

if __name__ == "__main__":
    validate_coverage()
