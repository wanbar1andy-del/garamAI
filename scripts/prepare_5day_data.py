
import pandas as pd
import glob
import os
import shutil

SRC_DIR = "GARAM_Data/minute/kr"
DEST_DIR = "GARAM_Data/5day_replay"
DAY1_DIR = "GARAM_Data/day1_replay"

TARGET_DATES = ['20251209', '20251210', '20251211', '20251212']

def prepare_5day_data():
    print("Preparing 5-Day Data...")
    os.makedirs(DEST_DIR, exist_ok=True)
    
    # 1. Copy Day 1 (Jan 02) Data first
    print("Copying Jan 02 data...")
    day1_files = glob.glob(os.path.join(DAY1_DIR, "*.csv"))
    for f in day1_files:
        if "summary" in f: continue
        shutil.copy(f, DEST_DIR)
        
    print(f"Copied {len(day1_files)} files from {DAY1_DIR}.")
    
    # 2. Extract History (Dec 9-12)
    # Filter Top 50 from extraction_summary of Day 1?
    # Or scanning all? Scanning all is safer.
    
    hist_files = glob.glob(os.path.join(SRC_DIR, "*.csv"))
    print(f"Scanning {len(hist_files)} history files...")
    
    cnt = 0
    for f in hist_files:
        sym = os.path.basename(f).replace(".csv", "")
        
        # Read
        try:
            # We only need specific dates.
            # Reading entire file is OK (it's < 10MB usually).
            df = pd.read_csv(f)
            
            # Format datetime
            col0 = df.columns[0]
            # Convert to string YYYYMMDD...
            df['dstr'] = df[col0].astype(str).str[:8] # First 8 chars
            
            # Filter
            mask = df['dstr'].isin(TARGET_DATES)
            filtered = df[mask].copy()
            
            if filtered.empty: continue
            
            # Standardize Columns for Backtrader
            # Hist: datetime, open, high, low, close, volume (desc)
            # Replay expects: ts, open, high, low, close, volume (asc)
            
            # Convert ts
            filtered['ts'] = pd.to_datetime(filtered[col0].astype(str), format='%Y%m%d%H%M%S')
            filtered = filtered.sort_values('ts')
            
            # Rename
            filtered = filtered[['ts', 'open', 'high', 'low', 'close', 'volume']]
            
            # Merge with existing Jan 02 file if exists
            dest_path = os.path.join(DEST_DIR, f"{sym}.csv")
            
            if os.path.exists(dest_path):
                # Append
                jan02_df = pd.read_csv(dest_path)
                # Jan02 usually has headers ts,open... 
                # Concat
                combined = pd.concat([filtered, jan02_df], ignore_index=True)
                combined['ts'] = pd.to_datetime(combined['ts'])
                combined = combined.sort_values('ts')
                combined.to_csv(dest_path, index=False)
            else:
                filtered.to_csv(dest_path, index=False)
                
            cnt += 1
            if cnt % 50 == 0: print(f"Processed {cnt}...")
            
        except Exception as e:
            print(f"Error {sym}: {e}")
            
    print("Done.")

if __name__ == "__main__":
    prepare_5day_data()
