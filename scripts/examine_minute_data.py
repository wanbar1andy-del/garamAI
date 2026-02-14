
import pandas as pd
import glob
import os
import numpy as np

def examine_data(data_dir):
    print(f"Exchanging Data in: {data_dir}")
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    print(f"Found {len(files)} CSV files.")
    
    if not files:
        print("No files found.")
        return

    # 1. Sample Check (First 5 + Random 5)
    import random
    random.seed(42)
    targets = files[:5] + random.sample(files[5:], 5) 
    
    if "005930.csv" in [os.path.basename(f) for f in files]:
        samsung = [f for f in files if "005930.csv" in f][0]
        if samsung not in targets:
            targets.append(samsung)

    print(f"\nScanning {len(targets)} sample files...")
    
    stats = []
    
    for f in targets:
        sym = os.path.basename(f).replace(".csv", "")
        try:
            df = pd.read_csv(f)
            # Standardize Columns
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Check required cols (Accept 'date' or 'datetime')
            req = ['open', 'high', 'low', 'close', 'volume']
            time_col = 'datetime' if 'datetime' in df.columns else 'date' if 'date' in df.columns else None
            
            missing = [c for c in req if c not in df.columns]
            if not time_col: missing.append('datetime/date')
            
            if missing:
                status = f"MISSING_COLS({missing})"
                start, end = "N/A", "N/A"
            else:
                # Convert Time
                df[time_col] = df[time_col].astype(str)
                # Check Sorting
                is_sorted_asc = df[time_col].is_monotonic_increasing
                is_sorted_desc = df[time_col].is_monotonic_decreasing
                
                if is_sorted_asc:
                    status = "OK (Asc)"
                    start = df[time_col].iloc[0]
                    end = df[time_col].iloc[-1]
                elif is_sorted_desc:
                    status = "OK (Desc) -> Needs Sort"
                    start = df[time_col].iloc[-1]
                    end = df[time_col].iloc[0]
                else:
                    status = "MIXED/UNSORTED"
                    start = df[time_col].min()
                    end = df[time_col].max()
            
            count = len(df)

                
            stats.append({
                'symbol': sym,
                'status': status,
                'count': count,
                'start': start,
                'end': end
            })
        except Exception as e:
            stats.append({'symbol': sym, 'status': f"ERROR: {str(e)}", 'count': 0, 'start':"", 'end':""})

    # Summary Table
    res_df = pd.DataFrame(stats)
    print(res_df.to_markdown(index=False))
    
    # Global Scan for outliers (File Size)
    sizes = [os.path.getsize(f) for f in files]
    avg_size = np.mean(sizes)
    min_size = np.min(sizes)
    max_size = np.max(sizes)
    
    print(f"\n[Global File Size Stats]")
    print(f"Avg: {avg_size/1024:.1f} KB")
    print(f"Min: {min_size/1024:.1f} KB")
    print(f"Max: {max_size/1024:.1f} KB")
    
    # Identify empty/tiny files
    tiny_files = [os.path.basename(files[i]) for i, s in enumerate(sizes) if s < 1024] # < 1KB
    if tiny_files:
        print(f"\n[WARNING] Found {len(tiny_files)} tiny files (potential corruption):")
        print(tiny_files[:10])

if __name__ == "__main__":
    examine_data("GARAM_Data/minute/kr")
