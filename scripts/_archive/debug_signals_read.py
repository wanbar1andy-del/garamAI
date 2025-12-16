import sys
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS
import json
import os

print(f"PATHS.STRATEGY_SIGNALS_LIVE: {PATHS.STRATEGY_SIGNALS_LIVE}")
if PATHS.STRATEGY_SIGNALS_LIVE.exists():
    print("File exists.")
    with open(PATHS.STRATEGY_SIGNALS_LIVE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"Keys: {list(data.keys())}")
        print(f"Equity: {data.get('equity')}")
        print(f"Holdings count: {len(data.get('holdings', {}))}")
else:
    print("File does NOT exist.")
