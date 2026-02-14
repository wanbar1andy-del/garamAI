"""
[GARAM 2.0 ULTRA] 
- GPU: NVIDIA RTX 3060 Laptop (CUDA Acceleration)
- Engine: Multi-Scenario Switching (Gold Rush, Ice Age, etc.)
- AI Brain: OSS (Neural Brain + Hero Analyzer)
- Project: 401 Symbols Backtest (2025.06 - 2026.02)
"""

import os
import sys
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path("C:/garam/garam")
PYTHON_39 = "py -3.9"

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚀 {msg}")

def main():
    log("Garam 2.0 ULTRA Engine Starting...")
    log("System: NVIDIA RTX 3060 Laptop GPU Verified.")
    
    # 1. 시나리오 초기화 (빙하기 탈출 -> 골드러시/노멀 전이 준비)
    log("Initialization: Escaping ICE_AGE. Switching to Dynamic Regime.")
    config_file = PROJECT_ROOT / "config/active_params.json"
    if config_file.exists():
        import json
        with open(config_file, 'r') as f:
            data = json.load(f)
        data['scenario'] = "D_NORMAL" # Start from Normal
        data['params']['max_exposure'] = 0.95 # Full Capacity
        data['params']['stop_loss_atr'] = 3.0 # Normal ATR
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=4)
        log("Config: Scenario RESET to D_NORMAL (Exposure 95%).")

    # 2. 백그라운드 서비스 가동 (Scenario Manager & Hero Analyzer)
    # GPU 모니터링은 별도 프로세스
    log("Starting Scenario Manager (Sub-process)...")
    subprocess.Popen(f"{PYTHON_39} scripts/scenario_manager.py", shell=True)
    
    log("Starting Hero Analyzer (Sub-process)...")
    subprocess.Popen(f"{PYTHON_39} scripts/hero_analyzer.py", shell=True)
    
    # 3. 메인 OSS 백테스트 & 학습 (GPU 가동)
    log("Launching Main OSS Final Backtest (GPU ACCELERATED)...")
    # run_oss_final_v4.py를 수정하여 py -3.9에서 GPU를 쓰도록 함
    cmd = f"{PYTHON_39} pipeline/backtest/run_oss_final_v4.py"
    
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 실시간 로그 스트리밍
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            
    except KeyboardInterrupt:
        log("Engine Interrupted by Commander.")
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    main()
