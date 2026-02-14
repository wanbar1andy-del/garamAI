
import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("C:/garam/garam")
CONFIG_FILE = PROJECT_ROOT / "config/active_params.json"

def run_commander():
    print(f"[{datetime.now()}] 👮 Garam Commander: Initiating Daily Protocol...")
    
    # 1. Regime Check (Using HeroAnalyzer Logic or simple heuristic?)
    # For independent robustness, we use `hero_analyzer.py` which does both.
    
    print(f"[{datetime.now()}] 🧠 Brain Scan: Running Hero Analyzer...")
    try:
        # Run Analyzer (It updates active_params.json internally)
        cmd = [sys.executable, str(PROJECT_ROOT / "scripts/hero_analyzer.py"), "--once"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode == 0:
            print("[Commander] Analyzer Success.")
            print(res.stdout)
        else:
            print("[Commander] Analyzer Failed!")
            print(res.stderr)
            
    except Exception as e:
        print(f"[Commander] Critical Error running Analyzer: {e}")

    # 2. Verify Config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            conf = json.load(f)
            scen = conf.get('scenario', 'UNKNOWN')
            heroes = conf.get('pyramid_weights', {})
            print(f"[Commander] 📜 Daily Orders Confirmed:")
            print(f"   - Scenario: {scen}")
            print(f"   - Heroes Targeted: {list(heroes.keys())}")
            
            if scen == "GOLD_RUSH":
                print(f"   - 🚀 GOLD RUSH DECLARED! Aggressive Pyramiding Active.")
            elif scen == "ICE_AGE":
                print(f"   - ❄️ ICE AGE WARNING! Defensive Shield Active (Max 10%).")
                
    else:
        print("[Commander] ⚠️ Config file not found. Defaulting to safe mode.")

if __name__ == "__main__":
    run_commander()
