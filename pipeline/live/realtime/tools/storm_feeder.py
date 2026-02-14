import time
import json
import uuid
import random
import argparse
from datetime import datetime, timedelta, timezone

def generate_event(seq, event_time, symbol="005930"):
    return {
        "event_id": uuid.uuid4().hex,
        "event_type": "BAR",
        "event_time": event_time.isoformat(),
        "ingest_time": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "seq": seq,
        "payload": {
            "open": 100 + seq % 10,
            "high": 110 + seq % 10,
            "low": 90 + seq % 10,
            "close": 105 + seq % 10,
            "volume": 1000 * seq
        }
    }

def run_storm(args):
    path = args.file_path
    count = args.count
    rate = args.rate
    delay = 1.0 / rate if rate > 0 else 0
    
    start_time = datetime.now(timezone.utc)
    
    print(f"[Feeder] generating {count} events to {path} at {rate} eps...")
    
    with open(path, 'a', encoding='utf-8') as f:
        for i in range(count):
            # Scenario Logic
            if args.scenario == "disorder":
                # Jitter time: -2s to +1s
                jitter = random.uniform(-2, 1)
                evt_time = start_time + timedelta(seconds=i + jitter)
            elif args.scenario == "late":
                # Occasional very late event (> 5s)
                is_late = (i % 50 == 0)
                if is_late:
                    evt_time = start_time + timedelta(seconds=i - 10)
                else:
                    evt_time = start_time + timedelta(seconds=i)
            else:
                # Normal monotonic
                evt_time = start_time + timedelta(seconds=i)
            
            evt = generate_event(i, evt_time)
            line = json.dumps(evt)
            
            # Partial Write Scenario
            if args.scenario == "partial" and i % 10 == 0:
                # Split line
                mid = len(line) // 2
                f.write(line[:mid])
                f.flush()
                time.sleep(0.01)
                f.write(line[mid:] + "\n")
            else:
                f.write(line + "\n")
            
            f.flush()
            
            if delay > 0:
                time.sleep(delay)
                
            if i % 100 == 0:
                print(f"[Feeder] Sent {i}/{count}")

    print("[Feeder] Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", default="GARAM_Data/live/feed.jsonl")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--rate", type=float, default=100)
    parser.add_argument("--scenario", choices=["normal", "disorder", "late", "partial"], default="normal")
    args = parser.parse_args()
    
    run_storm(args)
