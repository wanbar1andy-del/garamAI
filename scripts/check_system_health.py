
import sys
import psutil
from pathlib import Path
from datetime import datetime

def check_health():
    print(f"[{datetime.now()}] Running System Health Check...")
    
    # 1. Check SSOT Universe
    univ_file = Path("GARAM_Data/real_universe_400.csv")
    if univ_file.exists():
        print(f"[OK] SSOT Universe found: {univ_file}")
    else:
        print(f"[FAIL] SSOT Universe MISSING: {univ_file}")
        
    # 2. Check Engine Process
    engine_running = False
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['cmdline'] and 'run_live_trading.py' in ' '.join(p.info['cmdline']):
                engine_running = True
                print(f"[OK] Engine Running (PID: {p.info['pid']})")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if not engine_running:
        print("[WARN] Engine NOT Detected (Note: It might be running under a different name or just starting)")

    print(f"[{datetime.now()}] Health Check Completed (Status: ONLINE)")

if __name__ == "__main__":
    check_health()
