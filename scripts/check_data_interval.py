import sys
import os
import pandas as pd
from pathlib import Path

CACHE_FILE = Path("c:/garam/garam/cache/market_matrix_8m.pkl")

def check_interval():
    print("🔍 [DATA CHECK] Verifying Time Interval...")
    try:
        data = pd.read_pickle(CACHE_FILE)
        closes = data.get('closes')
        if closes is None: closes = data.get('close')
        
        idx = closes.index
        diff = idx[1] - idx[0]
        
        print(f"⏱️ Time Diff between Row 0 and Row 1: {diff}")
        print(f"   - Row 0: {idx[0]}")
        print(f"   - Row 1: {idx[1]}")
        
        if diff.seconds == 60:
            print("✅ CONFIRMED: 1-Minute Data (Real)")
        elif diff.seconds == 600:
            print("⚠️ WARNING: 10-Minute Data")
        elif diff.seconds == 3600:
            print("⚠️ WARNING: 60-Minute Data")
        else:
            print(f"❓ UNKNOWN INTERVAL: {diff}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_interval()
