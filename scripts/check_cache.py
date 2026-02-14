import pandas as pd
import pickle
from pathlib import Path

cache_path = Path("c:/garam/garam/cache/market_matrix_8m.pkl")

try:
    if cache_path.exists():
        data = pd.read_pickle(cache_path)
        if isinstance(data, dict):
             # It might be a dict with keys like 'closes', 'volumes'
             closes = data.get('closes')
             if closes is not None:
                 print(f"CACHE CHECK: Symbols={len(closes.columns)}")
             else:
                 print(f"CACHE CHECK: Keys={list(data.keys())}")
        elif isinstance(data, pd.DataFrame):
            print(f"CACHE CHECK: Symbols={len(data.columns)}")
        else:
            print("CACHE CHECK: Unknown format")
    else:
        print("CACHE CHECK: File Not Found")
except Exception as e:
    print(f"CACHE CHECK ERROR: {e}")
