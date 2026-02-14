
import psutil
import os
import sys

def boost_priority():
    print("=== GARAM System Booster ===")
    
    # 1. Self Elevation
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        print(f"[OK] Booster Process Priority Elevated to HIGH")
    except Exception as e:
        print(f"[Fail] Could not elevate booster: {e}")

    # 2. Boost Python Workers
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmd = proc.info['cmdline'] or []
                if any('garam' in arg for arg in cmd):
                    proc.nice(psutil.HIGH_PRIORITY_CLASS)
                    print(f"[Boost] Elevated PID {proc.info['pid']} ({' '.join(cmd[-1:])})")
                    count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    print(f"\n>> Total {count} Garam processes boosted to HIGH Priority.")
    print(">> CPU Scheduler will now favor Garam over background tasks.")

if __name__ == "__main__":
    try:
        boost_priority()
    except ImportError:
        print("Installing psutil for tuning...")
        os.system(f"{sys.executable} -m pip install psutil")
        boost_priority()
