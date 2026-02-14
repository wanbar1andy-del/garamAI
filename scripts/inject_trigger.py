
import json
import datetime

FEED_PATH = "C:/garam/garam/feed_live.jsonl"

# Event: Trigger Event (-40% PnL)
event = {
    "event_id": "test_tick_py_trigger",
    "event_type": "TICK",
    "event_time": "2026-01-05T01:42:00+09:00",
    "ingest_time": "2026-01-05T01:42:00+09:00",
    "symbol": "005930",
    "payload": {
        "price": 60000, # -40% from 100k entry
        "volume": 100
    }
}

# Flush Event (to advance watermark)
flush_event = {
    "event_id": "test_tick_py_post_trigger",
    "event_type": "TICK",
    "event_time": "2026-01-05T01:42:10+09:00",
    "ingest_time": "2026-01-05T01:42:10+09:00",
    "symbol": "005930",
    "payload": {
        "price": 60000,
        "volume": 100
    }
}

with open(FEED_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(event) + "\n")
    f.write(json.dumps(flush_event) + "\n")

print(f"Injected TRIGGER TICK (-40%) to {FEED_PATH}")
