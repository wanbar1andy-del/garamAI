import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pipeline.store.data_loader import StoreManager
from pipeline._02_validate.paths import get_validate_paths

def run_e2e_smoke_test():
    print("=== Phase 2 E2E Smoke Test ===")
    
    # 1. Validate Artifacts Check
    print("\n[1] Checking Validate Artifacts...")
    vpaths = get_validate_paths(project_root)
    validated_files = list(vpaths.validated_minute_dir.glob("*.csv"))
    if not validated_files:
        print("FAIL: No validated CSVs found. Run Validate step first.")
        return
    print(f"PASS: Found {len(validated_files)} validated CSVs.")
    
    # 2. StoreManager Universe Check
    print("\n[2] Checking StoreManager Universe...")
    store = StoreManager()
    try:
        univ = store.get_universe()
        if "symbol" not in univ.columns:
            print(f"FAIL: Universe missing 'symbol' column. Columns: {univ.columns.tolist()}")
            return
        print(f"PASS: Universe loaded. {len(univ)} symbols. Column 'symbol' exists.")
    except Exception as e:
        print(f"FAIL: Universe load exception: {e}")
        return

    # 3. StoreManager Data Load (Validated Gate)
    print("\n[3] Checking StoreManager Data Access (Gate)...")
    target_symbol = univ["symbol"].iloc[0]
    print(f"Testing load for: {target_symbol}")
    
    try:
        df = store.get_data(target_symbol)
        if df.empty:
            print("WARN: Store returned empty DataFrame (might be valid if file is empty)")
        else:
            # Check columns
            required = ["date", "open", "high", "low", "close", "volume"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                print(f"FAIL: Missing columns in loaded data: {missing}")
                return
            
            # Check Date Type (should be datetime because StoreManager converts it for legacy compatibility)
            if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                 print(f"FAIL: Date column is not datetime (Legacy adapter failed). Type: {df['date'].dtype}")
                 return

            print(f"PASS: Data loaded successfully. Rows: {len(df)}")
            print(df.head(2).to_string(index=False))
            
    except Exception as e:
        print(f"FAIL: Data load exception: {e}")
        return

    print("\n=== E2E Test Complete: SUCCESS ===")

if __name__ == "__main__":
    run_e2e_smoke_test()
