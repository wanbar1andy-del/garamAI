import subprocess
import threading
import sys
import time

def run_data_collector():
    print("[PIPELINE] Starting Data Collector...")
    subprocess.run([sys.executable, "scripts/realtime_data_collector.py"])

def main():
    print("=== GARAM Real-Time Pipeline Triggered ===")
    
    # 1) Data Collector (Background)
    t1 = threading.Thread(target=run_data_collector)
    t1.daemon = True
    t1.start()
    
    # Allow collector to start
    time.sleep(5)

    # 2) Batch backtest
    print("[PIPELINE] Starting Batch Backtest...")
    subprocess.run([sys.executable, "scripts/batch_edge_map_400.py"])

    # 3) EdgeMap Integration
    print("[PIPELINE] Integrating Edge Map...")
    subprocess.run([sys.executable, "scripts/edge_map_400.py"])

    # 4) Guard Recommendation
    print("[PIPELINE] Generating Guard Params...")
    subprocess.run([sys.executable, "scripts/auto_guard_param_reco.py"])

    # 4.5) Telegram Risk Alert (Added requirement)
    print("[PIPELINE] Broadcasting Risk Alert...")
    subprocess.run([sys.executable, "scripts/telegram_risk_alarm.py"])

    # 5) Real Time Simulator
    print("[PIPELINE] Starting Real-Time Simulator...")
    subprocess.run([sys.executable, "scripts/realtime_simulator.py"])

    print("[PIPELINE] COMPLETE")

if __name__ == "__main__":
    main()
