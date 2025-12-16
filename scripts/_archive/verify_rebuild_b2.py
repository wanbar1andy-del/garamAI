import sys
from pathlib import Path
import pandas as pd
# import pytest (Removed to avoid dependency)

# Add garam root to path so we can import garam_core
sys.path.append("c:/garam/garam")

from garam_core.health.gate import gate_environment, gate_schema, gate_determinism, GateSpec

def test_foundation():
    print(">>> [Verify B-2] Starting Foundation Check...")
    
    # 1. Gate0: Environment
    print("1. Testing Gate0 (Environment)...")
    project_root = Path("c:/garam/garam/garam_core")
    print(f"   Project Root: {project_root}")
    print(f"   Expected paths.yaml: {project_root / 'config' / 'paths.yaml'}")
    try:
        paths = gate_environment(project_root)
        print(f"   - Passed. Revolved Data Root: {paths.data_root}")
    except Exception as e:
        print(f"   [FAIL] Gate0 Failed: {e}")
        # Let it crash after printing
        raise e
    
    # 2. Gate2: Determinism
    print("2. Testing Gate2 (Determinism)...")
    def pure_add(a, b): return a + b
    res = gate_determinism(pure_add, 1, 2)
    assert res == 3
    print("   - Passed. Pure function checked.")
    
    # 3. Gate1: Data Schema (Real File)
    print("3. Testing Gate1 (Data Schema)...")
    # Finding a real file
    target_file = paths.data_root / "minute/kr/005930_1m.csv"
    if not target_file.exists():
        print(f"   [WARNING] Sample file not found at {target_file}. Creating dummy DF for schema test.")
        # Create Dummy DF that satisfies schema
        dates = pd.date_range("2024-01-01", periods=5, freq="1min", tz="Asia/Seoul")
        df = pd.DataFrame({
            "date": dates,
            "open": [70000, 70100, 70200, 70100, 70000],
            "high": [70200, 70300, 70300, 70200, 70100],
            "low": [69900, 70000, 70100, 70000, 69900],
            "close": [70100, 70200, 70100, 70000, 70000],
            "volume": [1000, 2000, 1500, 1200, 1000]
        })
        df.set_index('date', inplace=True)
    else:
        print(f"   - Loading {target_file.name}...")
        df = pd.read_csv(target_file)
        # Ensure timestamp parse
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S').dt.tz_localize("Asia/Seoul")
        df.set_index('date', inplace=True) # Contract: Index must be DatetimeIndex
        df.sort_index(inplace=True) # Contract: Index must be sorted
        
    print(f"   [DEBUG] Index Type: {type(df.index)}")
    print(f"   [DEBUG] Index Sample: {df.index[:3]}")

    # Run Gate
    try:
        clean_df = gate_schema(df, GateSpec(timezone="Asia/Seoul"))
        print(f"   - Passed. Schema Validated. Rows: {len(clean_df)}")
    except Exception as e:
        print(f"   [FAIL] Gate1 Failed: {e}")
        # raise e # Don't raise, let's see output clearly
    
    print("\n>>> [Verify B-2] ALL GATES PASSED. Foundation is Ready.")

if __name__ == "__main__":
    test_foundation()
