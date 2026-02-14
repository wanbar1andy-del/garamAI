
import re
import json
import sys
from pathlib import Path

def verify_file_content(path, patterns):
    """
    path: Path object
    patterns: list of regex strings
    Returns: list of missing patterns
    """
    if not path.exists():
        return [f"File not found: {path}"]
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    missing = []
    for p in patterns:
        if not re.search(p, content):
            missing.append(p)
            
    return missing

def verify_json_config(path, key_checks):
    """
    path: Path object
    key_checks: dict of key -> expected_value
    """
    if not path.exists():
        return [f"File not found: {path}"]
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        failures = []
        for k, v in key_checks.items():
            val = data.get(k)
            if val != v:
                failures.append(f"{k}: expected {v}, got {val}")
        return failures
    except Exception as e:
        return [f"JSON Parse Error: {e}"]

def main():
    print("[Integrity] Starting System Verification...")
    project_root = Path(__file__).parent.parent
    
    errors = []
    
    # 1. Verify Engine Logic (Scenario C)
    engine_path = project_root / "scripts/run_live_trading.py"
    engine_patterns = [
        r"t_weight = 0\.40",
        r"pnl_pct > 0\.03",
        r"pnl_pct > 0\.07"
    ]
    missing_engine = verify_file_content(engine_path, engine_patterns)
    if missing_engine:
        errors.append(f"Engine Logic Mismatch in {engine_path.name}: Missing {missing_engine}")
    else:
        print(f"[OK] Engine Logic Verified: {engine_path.name} (Scenario C Active)")

    # 2. Verify Config
    config_path = project_root / "config/failure_patterns.json"
    config_checks = {
        "penalty_multiplier": 0.8
    }
    config_errors = verify_json_config(config_path, config_checks)
    if config_errors:
        errors.append(f"Config Mismatch in {config_path.name}: {config_errors}")
    else:
         print(f"[OK] Config Verified: {config_path.name} (Penalty 0.8)")

    if errors:
        print("[FAIL] SYSTEM INTEGRITY CHECK FAILED:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)
    else:
        print("[OK] ALL SYSTEMS GO. INTEGRITY CONFIRMED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
