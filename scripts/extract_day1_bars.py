
import json
import pandas as pd
import os
from datetime import datetime

FEED_PATH = "GARAM_Data/feed/feed_live.jsonl"
OUT_DIR = "GARAM_Data/day1_replay"

def extract_bars():
    print(f"Extracting Bars from {FEED_PATH}...")
    os.makedirs(OUT_DIR, exist_ok=True)
    
    ticks = []
    
    # 1. Load TICKS
    with open(FEED_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                ev = json.loads(line)
                # Check Type
                if ev.get('event_type') != 'TICK':
                    # Support legacy/mixed types if needed
                    pass
                
                # Check Payload
                payload = ev.get('payload', {})
                if not payload: continue
                
                sym = ev.get('symbol')
                if not sym: continue
                
                # Time: event_time or ingest_time
                ts_str = ev.get('event_time') or ev.get('ingest_time')
                if not ts_str: continue
                
                price = float(payload.get('price', 0))
                vol = int(payload.get('volume', 0))
                
                if price > 0:
                    ticks.append({
                        'ts': ts_str,
                        'symbol': sym,
                        'price': price,
                        'volume': vol
                    })
            except:
                continue
                
    if not ticks:
        print("No ticks found.")
        return

    print(f"Loaded {len(ticks)} ticks. Processing...")
    df = pd.DataFrame(ticks)
    # coerce errors to avoid crash
    df['ts'] = pd.to_datetime(df['ts'], errors='coerce')
    df = df.dropna(subset=['ts'])
    
    # Strip Timezone
    if df['ts'].dt.tz is not None:
        df['ts'] = df['ts'].dt.tz_localize(None)
    
    # 2. Resample to 1-Minute Bars
    # Group by Symbol
    grouped = df.groupby('symbol')
    
    summary = []
    
    for sym, group in grouped:
        group = group.sort_values('ts').set_index('ts')
        
        # Resample 1T (Minute)
        ohlcv = group['price'].resample('1min').ohlc()
        v = group['volume'].resample('1min').sum()
        ohlcv['volume'] = v
        
        # Drop empty (no trade minutes? Forward fill close? No, Keep NaN or Drop)
        # Dropna for purity, or ffill for continuity?
        # Standard: dropna (gaps exist)
        ohlcv = ohlcv.dropna()
        
        if ohlcv.empty: continue
        
        # Save
        out_path = os.path.join(OUT_DIR, f"{sym}.csv")
        ohlcv.to_csv(out_path)
        
        # Stats
        ret = (ohlcv['close'].iloc[-1] - ohlcv['open'].iloc[0]) / ohlcv['open'].iloc[0] * 100
        summary.append({'symbol': sym, 'bars': len(ohlcv), 'return': ret, 'vol': ohlcv['volume'].sum()})
        
    # Summary
    sum_df = pd.DataFrame(summary).sort_values('return', ascending=False)
    print(f"\nExtracted {len(sum_df)} symbols.")
    print("Top 5 Extraction:")
    print(sum_df.head(5).to_markdown(index=False))
    
    sum_df.to_csv(os.path.join(OUT_DIR, "extraction_summary.csv"), index=False)

if __name__ == "__main__":
    extract_bars()
