
"""
Data Pool Integrator (SSOT Auditor)
-----------------------------------
Checks for missing data in the GARAM Data Pool and reports/fills gaps.
Targets:
- Minute Data (2024-2026)
- Short Selling Data (2025-2026)
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path("c:/garam/garam/GARAM_Data")
UNIVERSE_PATH = DATA_DIR / "real_universe_400.csv"

def audit_data_pool():
    print("=== GARAM Data Pool Audit ===")
    
    if not UNIVERSE_PATH.exists():
        print("[Error] Universe file not found.")
        return

    try:
        df = pd.read_csv(UNIVERSE_PATH, dtype=str)
        if "symbol" in df.columns:
            targets = df["symbol"].tolist()
        else:
            targets = df.iloc[:,0].tolist()
    except:
        print("[Error] Failed to load universe.")
        return

    print(f"Total Targets: {len(targets)}")
    
    # 1. Minute Data Check
    minute_dir = DATA_DIR / "history" / "minute"
    missing_minute = []
    
    for sym in targets:
        p = minute_dir / f"{sym}.csv"
        if not p.exists():
            missing_minute.append(sym)
            
    print(f"\n[Minute Data] Found: {len(targets)-len(missing_minute)} | Missing: {len(missing_minute)}")
    if missing_minute:
        print(f" -> Missing Samples: {missing_minute[:5]}...")

    # 2. Short Selling Check (2025)
    short_2025_dir = DATA_DIR / "history" / "short_selling" / "2025"
    missing_short_25 = []
    for sym in targets:
        p = short_2025_dir / f"{sym}.csv"
        if not p.exists():
            missing_short_25.append(sym)
            
    print(f"\n[Short Selling 2025] Found: {len(targets)-len(missing_short_25)} | Missing: {len(missing_short_25)}")
    
    # 3. Short Selling Check (2026)
    short_2026_dir = DATA_DIR / "history" / "short_selling" / "2026"
    missing_short_26 = []
    for sym in targets:
        p = short_2026_dir / f"{sym}.csv"
        if not p.exists():
            missing_short_26.append(sym)
            
    print(f"\n[Short Selling 2026] Found: {len(targets)-len(missing_short_26)} | Missing: {len(missing_short_26)}")

    # 4. Overall Integrity
    score = (3*len(targets) - len(missing_minute) - len(missing_short_25) - len(missing_short_26)) / (3*len(targets)) * 100
    print(f"\n>> Data Pool Integrity Score: {score:.1f}%")
    
    if score < 100:
        print(">> Action: Run ingestion scripts to fill gaps.")
        
if __name__ == "__main__":
    audit_data_pool()
