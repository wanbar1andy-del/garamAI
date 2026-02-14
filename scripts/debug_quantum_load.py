
import pandas as pd
import numpy as np
import os
from pathlib import Path

def debug():
    log = []
    def p(msg):
        print(msg)
        log.append(str(msg))
        
    try:
        base_path = Path('GARAM_Data/60day_replay_kst')
        files = list(base_path.glob("*.csv"))
        p(f"Found {len(files)} files.")
        
        if not files: return
        
        f = files[0]
        p(f"Testing file: {f}")
        
        df = pd.read_csv(f)
        p(f"Columns: {df.columns.tolist()}")
        p(f"Shape: {df.shape}")
        p(f"Head: {df.head(1).values.tolist()}")
        
        if 'ts' in df.columns:
            df.rename(columns={'ts':'date'}, inplace=True)
        elif 'datetime' in df.columns:
            df.rename(columns={'datetime':'date'}, inplace=True)
            
        req = ['date','open','high','low','close','volume']
        missing = [c for c in req if c not in df.columns]
        if missing:
            p(f"Missing columns: {missing}")
        else:
            p("All columns present.")
            
        df['date'] = df['date'].astype(str)
        df['day'] = df['date'].str.slice(0, 10)
        p(f"Day Head: {df['day'].head(1).tolist()}")
        
        agg_funcs = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        daily = df.groupby('day').agg(agg_funcs).reset_index()
        
        p(f"Daily Shape: {daily.shape}")
        p(f"Daily Head: {daily.head(3)}")
        p(f"Len > 20? {len(daily) > 20}")
        
    except Exception as e:
        p(f"Exception: {e}")
        import traceback
        p(traceback.format_exc())
    finally:
        with open("debug_output.txt", "w") as f:
            f.write("\n".join(log))

if __name__ == "__main__":
    debug()
