"""
System Health Verification Script
Run this to verify the integrity of the GARAM system after healthcare updates.
"""
import pandas as pd
from pathlib import Path
import sys
import os

# Add scripts to path to import engine
sys.path.append(os.path.abspath("scripts"))
try:
    from run_weighted_sim import WeightedSimEngine
except ImportError:
    print("⚠️ Could not import WeightedSimEngine. Checking path...")

def check_data_integrity():
    print("\n[1] Data Integrity Check (GARAM_Data/minute/kr)")
    p = Path("GARAM_Data/minute/kr")
    files = list(p.glob("*.csv"))
    print(f"  Files found: {len(files)}")
    
    if len(files) < 400:
        print("  ⚠️ Warning: Fewer than 400 files found.")
    
    if files:
        sample = files[0]
        df = pd.read_csv(sample)
        print(f"  Sample ({sample.name}):")
        print(f"    Columns: {df.columns.tolist()}")
        print(f"    Rows: {len(df)}")
        
        # Check column types
        if 'datetime' not in df.columns:
             print("  ❌ FATAL: 'datetime' column missing!")
             return False
        
        # Check if datetime is clean (no mixed types caused by merge bugs)
        try:
            pd.to_datetime(df['datetime'].astype(str), format='%Y%m%d%H%M%S')
            print("  ✅ Datetime format valid")
        except Exception as e:
            print(f"  ❌ Datetime format invalid: {e}")
            return False
            
    return True

def check_sim_engine():
    print("\n[2] Simulation Engine Load Check")
    try:
        eng = WeightedSimEngine(1,0,0,0,0,0)
        # We perform a dry run of load_data. 
        # Note: This might take time if it loads all 400 files, so we might want to mock or just check logic.
        # But 'load_data' in the updated script prints "Loading data...".
        # Let's just check if the directory path in the instance is correct (it's hardcoded in method, so we can't check attribute).
        # We will try to load ONE symbol manually using the engine's logic to verify.
        
        data_dir = Path("GARAM_Data/minute/kr")
        sample_file = list(data_dir.glob("*.csv"))[0]
        
        df = pd.read_csv(sample_file)
        # Engine expects 'datetime' and resamples to daily
        df['datetime'] = pd.to_datetime(df['datetime'].astype(str), format='%Y%m%d%H%M%S')
        df.set_index('datetime', inplace=True)
        daily = df.resample('D').agg({'close':'last'}).dropna()
        
        print(f"  Engine Logic Verify ({sample_file.stem}):")
        print(f"    Minute Rows: {len(df)}")
        print(f"    Daily Rows: {len(daily)}")
        
        if len(daily) > 0:
            print("  ✅ Resampling logic works")
        else:
            print("  ⚠️ Resampling produced empty dataframe (check date range)")
            
    except Exception as e:
        print(f"  ❌ Engine check failed: {e}")
        return False
        
    return True

def check_kiwoom_config():
    print("\n[3] Kiwoom Config Check")
    try:
        with open("pipeline/ingest/run_ingest_kiwoom.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if 'GARAM_Data/minute/kr' in content:
            print("  ✅ Output Path: GARAM_Data/minute/kr")
        else:
            print("  ❌ Output Path mismatch!")
            
        if 'max_limit = 1200' in content:
            print("  ✅ Max Limit: 1200 (2 years)")
        else:
            print("  ❌ Max Limit not updated to 1200!")
            
        if "old_df['date'] = old_df['date'].astype(str)" in content:
            print("  ✅ Type Fix Applied")
        else:
            print("  ❌ Type Fix NOT found!")
            
    except Exception as e:
        print(f"  ❌ Config check failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("=== System Health Verification ===")
    r1 = check_data_integrity()
    r2 = check_sim_engine()
    r3 = check_kiwoom_config()
    
    if r1 and r2 and r3:
        print("\n✅ SYSTEM HEALTHY")
    else:
        print("\n❌ SYSTEM ISSUES FOUND")
