
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.live.realtime.file_consumer import FileTailConsumer

FEED_PATH = "C:/garam/garam/feed_live.jsonl"
print(f"Feeding from {FEED_PATH}")

if not os.path.exists(FEED_PATH):
    print("File not found")
    sys.exit(1)

print(f"File size: {os.path.getsize(FEED_PATH)}")

c = FileTailConsumer(FEED_PATH)
print("Consumer initialized")

for i in range(10):
    evt = c.poll(0.1)
    if evt:
        print(f"READ EVENT: {evt}")
        break
    else:
        print(f"Poll {i}: None")
        time.sleep(0.5)

c.close()
