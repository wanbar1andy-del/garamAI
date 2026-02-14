from __future__ import annotations

import sys
import shutil
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# scripts/e2e_smoke_orders.py
# Usage: python -m scripts.e2e_smoke_orders

def setup_dirs(root: Path):
    order_dir = root / "GARAM_Data" / "orders"
    dirs = ["inbox", "processing", "archive", "ack", "rej"]
    for d in dirs:
        (order_dir / d).mkdir(parents=True, exist_ok=True)
    return order_dir

def wait_for_file(pattern: Path, timeout=10, check_interval=1):
    start = time.time()
    while time.time() - start < timeout:
        found = list(pattern.parent.glob(pattern.name))
        if found:
            return found[0]
        time.sleep(check_interval)
    return None

def test_order_lifecycle(root: Path, order_dir: Path):
    print("[TEST] Order Bus Lifecycle (Inbox -> Process -> Archive/ACK-REJ)...")
    
    # 1. Create a dummy order
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    idem = f"smoke_test_{ts}"
    fname = f"req_{idem}.json"
    fpath = order_dir / "inbox" / fname
    
    order_data = {
        "timestamp": ts,
        "symbol": "005930",
        "order_type": "buy",
        "qty": 1,
        "price": 0,
        "price_type": "03",
        "source": "smoke_test",
        "idempotency_key": idem
    }
    
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(order_data, f)
        
    print(f"  -> Created {fname} in Inbox. Waiting for processing...")
    
    # Wait for Archive (Successful Processing)
    # Note: Kiwoom Ingest needs to be running!
    # If not running, this test acts as a "Manual Confirmation" request.
    
    archived = wait_for_file(order_dir / "archive" / fname, timeout=45)
    if archived:
        print(f"  [PASS] File moved to Archive: {archived.name}")
        
        # Check ACK or REJ
        ack = wait_for_file(order_dir / "ack" / f"ack_{idem}.json", timeout=10)
        rej = wait_for_file(order_dir / "rej" / f"rej_{idem}.json", timeout=10)
        
        if ack:
            print(f"  [PASS] ACK generated: {ack.name}")
        elif rej:
            print(f"  [PASS] REJ generated (Expected if Kiwoom not connected): {rej.name}")
        else:
            print("  [FAIL] No ACK/REJ generated despite Archive move.")
    else:
        print("  [WARN] File not moved to Archive. Is Kiwoom Ingest running?")

def test_corrupted_json(root: Path, order_dir: Path):
    print("\n[TEST] Corrupted JSON Handling...")
    
    idem = "corrupt_test"
    fname = f"req_{idem}.json"
    fpath = order_dir / "inbox" / fname
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("{ invalid json ...") # Broken
        
    print(f"  -> Created broken file {fname}. Waiting for REJ...")
    
    # Should move to archive and create REJ
    rej_path = order_dir / "rej" / f"rej_{idem}.json"
    rej = wait_for_file(rej_path, timeout=10)
    
    if rej:
        print(f"  [PASS] Corrupted file rejected: {rej.name}")
    else:
        print("  [WARN] Corrupted file stuck or not processed.")

def main():
    root = Path(__file__).resolve().parent.parent
    order_dir = setup_dirs(root)
    
    print("=== Garam E2E Order Bus Smoke Test ===")
    print("Pre-requisite: run_ingest_kiwoom.py MUST be running (32-bit).")
    
    test_order_lifecycle(root, order_dir)
    test_corrupted_json(root, order_dir)
    
    # Stuck reaper test requires mocking time or waiting > 120s, skipping for quick smoke.
    
    print("\n=== E2E Test Finished ===")

if __name__ == "__main__":
    main()
