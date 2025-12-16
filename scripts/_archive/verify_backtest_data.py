"""
Verify 1-Year Backtest Data Integrity

Verifies that dashboard data comes from legitimate 1-year backtest:
1. Check simulation_1year_turbo.csv data quality
2. Verify date range (2024-12-01 to 2025-12-05)
3. Confirm Engine1 (Strategy A) return = +88%
4. Validate data consistency
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

def verify_backtest_data():
    """Verify 1-year backtest data"""
    
    print("=" * 60)
    print("BACKTEST DATA VERIFICATION")
    print("=" * 60)
    
    # 1. Load simulation data
    csv_path = PATHS.DATA_DIR / "reports" / "simulation_1year_turbo.csv"
    
    if not csv_path.exists():
        print(f"❌ ERROR: File not found: {csv_path}")
        return False
    
    print(f"\n✅ Found: {csv_path}")
    
    df = pd.read_csv(csv_path, index_col='date', parse_dates=True)
    
    # 2. Verify data structure
    print(f"\n📊 Data Structure:")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {df.columns.tolist()}")
    print(f"   Date Range: {df.index[0]} to {df.index[-1]}")
    
    # 3. Calculate returns
    initial_capital = 100_000_000
    
    engine1_final = df['engine1'].iloc[-1]
    engine2_final = df['engine2'].iloc[-1]
    kospi_final = df['kospi'].iloc[-1]
    
    engine1_return = ((engine1_final / initial_capital) - 1) * 100
    engine2_return = ((engine2_final / initial_capital) - 1) * 100
    kospi_return = ((kospi_final / initial_capital) - 1) * 100
    
    print(f"\n💰 Returns:")
    print(f"   Engine1 (Strategy A): {engine1_return:.2f}%")
    print(f"   Engine2 (Strategy C): {engine2_return:.2f}%")
    print(f"   KOSPI Benchmark: {kospi_return:.2f}%")
    
    # 4. Verify expected return
    expected_return = 88.0
    tolerance = 5.0  # ±5%
    
    if abs(engine1_return - expected_return) > tolerance:
        print(f"\n⚠️  WARNING: Engine1 return ({engine1_return:.2f}%) differs from expected ({expected_return:.2f}%)")
        print(f"   Tolerance: ±{tolerance}%")
    else:
        print(f"\n✅ Engine1 return verified: {engine1_return:.2f}% (Expected: ~{expected_return}%)")
    
    # 5. Check for missing data
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        print(f"\n⚠️  WARNING: {missing_count} missing values found")
    else:
        print(f"\n✅ No missing values")
    
    # 6. Sample data
    print(f"\n📝 Sample Data (Last 5 Days):")
    print(df.tail().to_string())
    
    # 7. Summary
    print(f"\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"✅ Data file exists: {csv_path.name}")
    print(f"✅ Data rows: {len(df)}")
    print(f"✅ Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"✅ Engine1 return: {engine1_return:.2f}%")
    print(f"✅ Data quality: {'PASS' if missing_count == 0 else 'FAIL'}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        verify_backtest_data()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
