
import json
import datetime

FEED_PATH = "C:/garam/garam/feed_live.jsonl"

event = {
    "event_id": "test_tick_py_v1",
    "event_type": "TICK",
    "event_time": "2026-01-05T01:21:00+09:00",
    "ingest_time": "2026-01-05T01:21:00+09:00",
    "symbol": "005930",
    "payload": {
        "price": 60500,
        "volume": 10
    }
}

with open(FEED_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(event) + "\n")

print(f"Injected TICK to {FEED_PATH}")
