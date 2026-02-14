
import json
import pandas as pd
from datetime import datetime

FEED_PATH = "GARAM_Data/feed/feed_live.jsonl"

def scan_heroes():
    print(f"Scanning {FEED_PATH} for Heroes...")
    
    data = {} # sym -> {open, close, vol}
    
    try:
        with open(FEED_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    ev = json.loads(line)
                    sym = ev.get('symbol')
                    payload = ev.get('payload', {})
                    if not payload: continue
                    
                    price = float(payload.get('price', 0))
                    vol = int(payload.get('volume', 0))
                    
                    if not sym or price == 0: continue
                    
                    if sym not in data:
                        data[sym] = {'open': price, 'close': price, 'vol': 0}
                    
                    data[sym]['close'] = price
                    data[sym]['vol'] += vol # Cumulative? Or tick vol? Usually tick vol.
                    
                except:
                    continue
                    
        # Calc Stats
        results = []
        for sym, stats in data.items():
            op = stats['open']
            cl = stats['close']
            if op > 0:
                ret = (cl - op) / op * 100.0
                results.append({
                    'symbol': sym,
                    'return': ret,
                    'close': cl,
                    'volume': stats['vol']
                })
        
        # Sort
        df = pd.DataFrame(results)
        if df.empty:
            print("No data found.")
            return

        df = df.sort_values('return', ascending=False)
        
        print("\n=== TODAY'S TOP 10 HERO CANDIDATES (Raw Feed) ===")
        print(df.head(10).to_markdown(index=False))
        
        print("\n=== TODAY'S WORST 5 ===")
        print(df.tail(5).to_markdown(index=False))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_heroes()
