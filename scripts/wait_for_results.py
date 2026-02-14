
import time
import sys
import json
from pathlib import Path

TARGET = Path("c:/garam/garam/config/active_strategy_params.json")

print("Waiting for training results...", flush=True)
timeout = 60 # wait 60 seconds
start = time.time()

while time.time() - start < timeout:
    if TARGET.exists():
        # Check if it was modified recently (to ensure it's this run's result)
        # But for now existence is enough as previous run failed or didn't create it.
        try:
            with open(TARGET, "r") as f:
                data = json.load(f)
            print("\n[SUCCESS] Training Completed!")
            print(json.dumps(data, indent=2))
            sys.exit(0)
        except:
            pass
    time.sleep(2)

print("\n[PENDING] Training is still in progress...")
sys.exit(0)
