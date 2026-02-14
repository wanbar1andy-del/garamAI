
import subprocess
import time
from datetime import datetime
import sys
import os

def run_auto_pilot():
    print("=========================================")
    print("  🚀 ANTI-GRAVITY AUTO-PILOT ENGAGED")
    print("  System: GARAM 2.1 (Pyramid Engine)")
    print(f"  Start Time: {datetime.now()}")
    print("=========================================")
    
    # 0. Boot Integrity Check
    print("[AutoPilot] Running System Integrity Check...")
    try:
        # Force encoding to utf-8 for subprocess communication, but standard text output is safest
        check_result = subprocess.run([sys.executable, "scripts/verify_system_integrity.py"], capture_output=True, text=True, encoding='utf-8')
        print(check_result.stdout)
        if check_result.returncode != 0:
            print("[AutoPilot] [CRITICAL] Integrity Check Failed!")
            print(check_result.stderr)
            # We might want to halt or alert here. For now, we continue with loud warning.
            # In a real rigorous system, we might exit.
            print("[AutoPilot] WARNING: Proceeding with potentially compromised system configuration.")
        else:
            print("[AutoPilot] [OK] Integrity Verified. Proceeding.")
            
    except Exception as e:
        print(f"[AutoPilot] Failed to run integrity check: {e}")

    
    # State
    trading_process = None
    
    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # 1. Morning Briefing (08:30)
        if current_time_str == "08:30" and now.second < 10:
            print(f"[{now}] 🌅 Morning Protocol Initiated.")
            subprocess.run([sys.executable, "scripts/garam_commander.py"])
            time.sleep(60) # Avoid repeat
            
        # 2. Market Open (09:00)
        if current_time_str == "09:00" and now.second < 10:
            if trading_process is None or trading_process.poll() is not None:
                print(f"[{now}] 🔔 Market Open! Launching Engine...")
                # Launch Live Trading
                trading_process = subprocess.Popen([
                    sys.executable, "scripts/run_live_trading.py",
                    "--config", "config/profile_champion_v3_weighted_400.yaml",
                    "--mode", "paper" # Default to Paper for safety unless Real flag
                ])
                time.sleep(60)
                
        # 3. Health Check (Every 1 min)
        if trading_process and trading_process.poll() is not None:
             print(f"[{now}] ⚠️ Engine Died! Restarting in 5s...")
             time.sleep(5)
             trading_process = subprocess.Popen([
                 sys.executable, "scripts/run_live_trading.py",
                 "--config", "config/profile_champion_v3_weighted_400.yaml",
                 "--mode", "paper"
             ])
             
        # 4. Market Close (15:35)
        if current_time_str == "15:35":
            if trading_process:
                print(f"[{now}] 🌙 Market Close. Initializing Shutdown...")
                trading_process.terminate()
                trading_process = None
                print(f"[{now}] System Sleep.")
                
                # 4.1 Daily Report
                print(f"[{now}] 📝 Sending Daily Trade Report...")
                try:
                    subprocess.run([sys.executable, "scripts/report/report_daily_trades.py"])
                except Exception as e:
                    print(f"Failed to send report: {e}")
                    
                time.sleep(60)

        # 5. Self-Learning Loop (23:00)
        if current_time_str == "23:00" and now.second < 10:
            print(f"[{now}] 🧠 Post-Mortem Analysis Initiated.")
            subprocess.run([sys.executable, "scripts/oss_post_mortem.py"])
            time.sleep(60)
                
        time.sleep(1)

if __name__ == "__main__":
    run_auto_pilot()
