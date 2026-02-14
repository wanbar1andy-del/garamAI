
import json
import datetime

FEED_PATH = "C:/garam/garam/feed_live.jsonl"

# Event 2: Flush Event (10 seconds later)
event = {
    "event_id": "test_tick_py_flush",
    "event_type": "TICK",
    "event_time": "2026-01-05T01:21:10+09:00",
    "ingest_time": "2026-01-05T01:21:10+09:00",
    "symbol": "005930",
    "payload": {
        "price": 60600,
        "volume": 10
    }
}

with open(FEED_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(event) + "\n")

print(f"Injected FLUSH TICK to {FEED_PATH}")
