
import pandas as pd
import glob
import os
import datetime as dt

IN_DIR = "GARAM_Data/history/minute"
OUT_DIR = "GARAM_Data/60day_replay_kst"
os.makedirs(OUT_DIR, exist_ok=True)

REF_SYMBOL = "005930" # Samsung Electronics as Calendar Reference

def get_last_60_days():
    # Find reference file
    pattern = os.path.join(IN_DIR, f"{REF_SYMBOL}.csv")
    files = glob.glob(pattern)
    if not files:
        print("Reference file not found.")
        return []
    
    df = pd.read_csv(files[0])
    # Parse date column YYYYMMDDHHMMSS
    df['dt'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
    df['day'] = df['dt'].dt.date
    unique_days = sorted(df['day'].dropna().unique())
    
    last_60 = unique_days[-60:]
    print(f"Identified {len(last_60)} days from {last_60[0]} to {last_60[-1]}")
    return set(last_60)

def normalize_file(fp, target_days):
    sym = os.path.basename(fp)
    try:
        df = pd.read_csv(fp)
        # Standardize Columns
        # History has: date, open, high, low, close, volume
        # We want: ts, open, high, low, close, volume (where ts is standard datetime string)
        
        df['ts'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
        if df['ts'].isnull().all(): return # Skip garbage
        
        # Filter by Target Days
        df['day'] = df['ts'].dt.date
        df = df[df['day'].isin(target_days)]
        
        if df.empty: return

        # Timezone Hygiene & Trim
        # Note: History data '20241202090000' usually implies KST 09:00 if collected from Kiwoom.
        # But per User request, we apply strict 09:00-15:30 filter.
        t = df['ts'].dt.time
        start_t = dt.time(9, 0)
        end_t = dt.time(15, 30)
        df = df[(t >= start_t) & (t <= end_t)]
        
        if df.empty: return

        # Output Format
        df = df[['ts', 'open', 'high', 'low', 'close', 'volume']].copy()
        df = df.sort_values('ts').drop_duplicates(subset=['ts'], keep='last')
        
        out_fp = os.path.join(OUT_DIR, sym)
        df.to_csv(out_fp, index=False)
        # print(f"Saved {sym}") # noisy
        
    except Exception as e:
        print(f"Error {sym}: {e}")

def run():
    target_days = get_last_60_days()
    if not target_days: return
    
    files = glob.glob(os.path.join(IN_DIR, "*.csv"))
    print(f"Processing {len(files)} files...")
    
    count = 0
    for i, fp in enumerate(files):
        normalize_file(fp, target_days)
        count += 1
        if count % 50 == 0:
            print(f"Processed {count}/{len(files)}")
            
    print("Done. Normalized data in:", OUT_DIR)

if __name__ == "__main__":
    run()
