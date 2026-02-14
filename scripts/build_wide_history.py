
import pandas as pd
import glob
import os
import tqdm
from datetime import datetime

def parse_datetime(s):
    # Vectorized or smart parsing
    s = str(s)
    if len(s) == 14: # 20251212091900
        return pd.to_datetime(s, format='%Y%m%d%H%M%S', errors='coerce')
    else:
        return pd.to_datetime(s, errors='coerce')

def build_wide_dataset(data_dir, output_dir):
    print(f"Building Wide Dataset from {data_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    print(f"Found {len(files)} files.")
    
    all_close = []
    all_vol = []
    
    # Process each file
    for f in tqdm.tqdm(files):
        try:
            sym = os.path.basename(f).replace(".csv", "")
            df = pd.read_csv(f)
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Identify Time Col
            time_col = 'datetime' if 'datetime' in df.columns else 'date' if 'date' in df.columns else None
            if not time_col:
                print(f"SKIP {sym}: No time column")
                continue
                
            # Normalize Time
            # Use explicit conversion for speed, fallback to auto
            # Check first element to guess format
            first = str(df[time_col].iloc[0])
            if len(first) == 14 and first.isdigit():
                 df['ts'] = pd.to_datetime(df[time_col], format='%Y%m%d%H%M%S', errors='coerce')
            else:
                 df['ts'] = pd.to_datetime(df[time_col], errors='coerce')
            
            # Sort Ascending
            df = df.sort_values('ts').set_index('ts')
            
            # Remove duplicates
            df = df[~df.index.duplicated(keep='last')]
            
            # Extract
            if 'close' in df.columns:
                s_close = df['close'].astype(float).rename(sym)
                all_close.append(s_close)
            
            if 'volume' in df.columns:
                s_vol = df['volume'].astype(float).rename(sym)
                all_vol.append(s_vol)
                
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    print("Merging Close Price Data...")
    wide_close = pd.concat(all_close, axis=1)
    wide_close = wide_close.sort_index()
    # Forward Fill (User Requirement)
    wide_close = wide_close.ffill()
    
    print("Merging Volume Data...")
    wide_vol = pd.concat(all_vol, axis=1)
    wide_vol = wide_vol.sort_index()
    # Volume: Fill with 0 (No trade)
    wide_vol = wide_vol.fillna(0)
    
    # Save
    print("Saving to Disk...")
    
    # Parquet (Fast)
    wide_close.to_parquet(os.path.join(output_dir, "wide_close.parquet"))
    wide_vol.to_parquet(os.path.join(output_dir, "wide_volume.parquet"))
    
    # CSV (User Readable - Spreadsheet)
    # Warning: Huge files, maybe sample? No, user wants full.
    wide_close.to_csv(os.path.join(output_dir, "wide_close.csv"))
    wide_vol.to_csv(os.path.join(output_dir, "wide_volume.csv"))
    
    print(f"Done. Saved to {output_dir}")
    print(f"Shape: {wide_close.shape}")

if __name__ == "__main__":
    build_wide_dataset("GARAM_Data/minute/kr", "GARAM_Data/unified")
