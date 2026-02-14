
import os

FEED_PATH = "C:/garam/garam/feed_live.jsonl"

# 1. Reset File (UTF-8 No BOM)
with open(FEED_PATH, "w", encoding="utf-8") as f:
    f.write("")

print(f"Reset {FEED_PATH}")
