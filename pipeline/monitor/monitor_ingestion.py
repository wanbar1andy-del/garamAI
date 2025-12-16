# scripts/monitor_ingestion.py
import time
import sys
from pathlib import Path
from datetime import datetime

def main():
    print(">>> Monitoring Ingestion Progress (Press Ctrl+C to stop)...")
    
    data_dir = Path("c:/garam/garam/GARAM_Data/history/minute")
    if not data_dir.exists():
        print(f"Waiting for directory creation: {data_dir}")
        time.sleep(5)
    
    last_count = 0
    start_time = time.time()
    
    while True:
        try:
            files = list(data_dir.glob("*.csv"))
            count = len(files)
            
            # Find recently modified
            recent = []
            now = time.time()
            for f in files:
                mtime = f.stat().st_mtime
                if (now - mtime) < 60: # modified in last minute
                    recent.append(f.name)
            
            # Sort recent by name
            recent.sort()
            
            # Speed calc
            elapsed = time.time() - start_time
            if elapsed > 0:
                speed = (count - last_count) / elapsed if last_count > 0 else 0
            
            # Clear screen (simulated with newlines)
            print("\n" * 2)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status Report")
            print(f"Total Symbols: {count}")
            print(f"Active (Last 1m): {len(recent)}")
            if recent:
                print(f"Latest Updates: {', '.join(recent[:5])} ...")
            
            if len(recent) == 0 and count > 0:
                print(">> No activity detected. Is the batch file running?")
            elif len(recent) > 0:
                print(">> Ingestion ACTIVE 🟢")
            
            last_count = count
            time.sleep(5)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
