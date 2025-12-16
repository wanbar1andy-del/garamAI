"""
System Health Monitor
Checks the heartbeat logs and system status to detect silent failures.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS

def check_health():
    print("[HEALTH] Checking System Health...")
    
    health_dir = PATHS.LOGS_DIR / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    
    heartbeat_file = health_dir / "heartbeat.log"
    
    if not heartbeat_file.exists():
        print("[CRITICAL] No heartbeat log found!")
        return False
        
    # Read last lines
    try:
        with open(heartbeat_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[ERROR] Error reading heartbeat log: {e}")
        return False
        
    if not lines:
        print("[CRITICAL] Heartbeat log is empty!")
        return False
        
    # Check freshness
    last_line = lines[-1]
    # Format: [TIMESTAMP] [COMPONENT] [STATUS] [METRICS]
    # Example: [2025-11-27 10:00:00] [DGE] [OK] [Signals: 5]
    
    try:
        timestamp_str = last_line.split(']')[0].strip('[')
        last_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        now = datetime.now()
        diff = now - last_time
        
        if diff > timedelta(hours=24):
            print(f"[CRITICAL] System silent for {diff}. Last heartbeat: {last_time}")
            return False
        elif diff > timedelta(hours=1):
            print(f"[WARNING] System silent for {diff}. Last heartbeat: {last_time}")
        else:
            print(f"[OK] System Active. Last heartbeat: {last_time}")
            
    except Exception as e:
        print(f"[WARNING] Error parsing last heartbeat: {e}")
        print(f"Last line: {last_line}")
        
    # Check for specific component failures in recent logs
    recent_errors = 0
    for line in lines[-50:]: # Check last 50 lines
        if "[ERROR]" in line or "[DEGRADED]" in line:
            recent_errors += 1
            
    if recent_errors > 0:
        print(f"[WARNING] Found {recent_errors} error/degraded statuses in recent logs.")
    else:
        print("[OK] No recent errors found.")
        
    return True

if __name__ == "__main__":
    success = check_health()
    sys.exit(0 if success else 1)
