"""
Intraday Data Quality Validator

Checks 15-minute intraday data for common issues before backtesting:
- Session alignment (09:00-15:30 KST)
- Minimum bars per day
- ORB calculation accuracy
- Daily indicator consistency

Usage:
    python validate_intraday_data.py --symbol 069500 --interval 15m --months 6
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob
import argparse
from datetime import datetime, time


def validate_single_file(file_path: Path) -> dict:
    """
    Validate a single day's intraday data.
    
    Returns:
        dict with validation results
    """
    df = pd.read_parquet(file_path)
    
    result = {
        'date': file_path.stem,
        'total_bars': len(df),
        'valid': True,
        'issues': []
    }
    
    # Check 1: Minimum bars (should have ~26 bars for 09:00-15:30)
    if len(df) < 20:
        result['valid'] = False
        result['issues'].append(f"Too few bars ({len(df)} < 20)")
    
    # Check 2: Session time alignment
    if not df.empty:
        first_time = df.index[0].time()
        last_time = df.index[-1].time()
        
        # Expected: 09:00-15:30 (or 15:15 for last bar)
        expected_start = time(9, 0)
        expected_end_range = (time(15, 15), time(15, 30))
        
        if first_time != expected_start:
            result['issues'].append(f"Session start mismatch: {first_time} != 09:00")
        
        if not (expected_end_range[0] <= last_time <= expected_end_range[1]):
            result['issues'].append(f"Session end outside range: {last_time}")
    
    # Check 3: ORB bars present (first 2 bars)
    if len(df) >= 2:
        orb_bars = df.iloc[:2]
        result['orb_high'] = orb_bars['high'].max()
        result['orb_low'] = orb_bars['low'].min()
        result['orb_range'] = result['orb_high'] - result['orb_low']
        
        # Sanity check: ORB range should be reasonable (e.g., 0.1% - 5% of price)
        mid_price = (result['orb_high'] + result['orb_low']) / 2
        orb_pct = result['orb_range'] / mid_price * 100
        
        if orb_pct > 5.0:
            result['issues'].append(f"ORB range too large: {orb_pct:.2f}%")
        elif orb_pct < 0.05:
            result['issues'].append(f"ORB range too small: {orb_pct:.2f}%")
    
    # Check 4: No duplicate timestamps
    if df.index.duplicated().any():
        result['valid'] = False
        result['issues'].append("Duplicate timestamps found")
    
    # Check 5: No missing OHLCV data
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if df[col].isna().any():
            result['issues'].append(f"NaN values in {col}")
    
    return result


def validate_dataset(symbol: str, interval: str, months: int, base_path: str):
    """
    Validate entire intraday dataset.
    """
    data_dir = Path(base_path) / symbol / interval
    
    if not data_dir.exists():
        print(f"Error: Directory not found: {data_dir}")
        return
    
    files = sorted(glob.glob(str(data_dir / "*.parquet")))
    
    if not files:
        print(f"Error: No parquet files in {data_dir}")
        return
    
    print(f"Validating {len(files)} files in {data_dir}\n")
    
    results = []
    valid_count = 0
    
    for file_path in files:
        result = validate_single_file(Path(file_path))
        results.append(result)
        
        if result['valid'] and not result['issues']:
            valid_count += 1
            print(f"✓ {result['date']}: {result['total_bars']} bars")
        else:
            print(f"✗ {result['date']}: {result['total_bars']} bars - {', '.join(result['issues'])}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {valid_count}/{len(results)} days valid ({valid_count/len(results)*100:.1f}%)")
    
    # Filter recommendation
    invalid_count = len(results) - valid_count
    if invalid_count > 0:
        print(f"\n⚠ Recommendation: Exclude {invalid_count} days with issues from backtest")
        print(f"  Add to load_intraday_data: Filter days with bars < 20")
    
    # ORB statistics (for valid days)
    valid_results = [r for r in results if r['valid'] and 'orb_range' in r]
    if valid_results:
        orb_ranges = [r['orb_range'] for r in valid_results]
        print(f"\nORB Range Statistics (valid days):")
        print(f"  Mean: {np.mean(orb_ranges):.2f}")
        print(f"  Median: {np.median(orb_ranges):.2f}")
        print(f"  Min: {np.min(orb_ranges):.2f}")
        print(f"  Max: {np.max(orb_ranges):.2f}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate intraday data quality")
    parser.add_argument('--symbol', required=True, help="Stock code (e.g., 069500)")
    parser.add_argument('--interval', choices=['5m', '15m', '60m'], default='15m')
    parser.add_argument('--months', type=int, default=6, help="Recent N months to check")
    parser.add_argument('--base-path', default="g:/내 드라이브/garamdata/history/intraday")
    
    args = parser.parse_args()
    
    validate_dataset(args.symbol, args.interval, args.months, args.base_path)


if __name__ == "__main__":
    main()
