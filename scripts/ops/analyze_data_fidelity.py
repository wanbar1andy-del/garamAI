"""
Data Fidelity Analyzer
Purpose: Audit 'GARAM_Data/60day_replay_kst' to verify effective minute data duration.
User suspects data is not valid minute data for the whole period.
"""
import glob
import os
import pandas as pd
import numpy as np
from pathlib import Path

def analyze_fidelity():
    root_dir = Path("C:/garam/garam/GARAM_Data/60day_replay_kst")
    files = list(root_dir.glob("*.csv"))
    
    if not files:
        print(f"No files found in {root_dir}")
        return

    print(f"Scanning {len(files)} files...")
    
    # Store stats per date
    date_counts = {} # date -> list of row counts
    
    # Sample first 20 files for speed, or all if small
    sample_files = files[:50] 
    
    total_files = len(sample_files)
    
    for i, f in enumerate(sample_files):
        try:
            df = pd.read_csv(f)
            # Ensure ts column
            col_map = {'ts': 'date', 'date': 'date', 'Date': 'date'}
            target_col = None
            for c in df.columns:
                if c in col_map:
                    target_col = c
                    break
            
            if not target_col:
                continue
                
            # Fast parse
            df['day'] = pd.to_datetime(df[target_col]).dt.date
            
            counts = df.groupby('day').size()
            
            for d, c in counts.items():
                if d not in date_counts:
                    date_counts[d] = []
                date_counts[d].append(c)
                
        except Exception as e:
            print(f"Error reading {f.name}: {e}")

    # Aggregating
    print("\n[Data Fidelity Report]")
    print(f"Analyzed {total_files} symbols.\n")
    print(f"{'Date':<12} | {'Avg Rows':<10} | {'Min Rows':<10} | {'Max Rows':<10} | {'Verdict'}")
    print("-" * 65)
    
    sorted_dates = sorted(date_counts.keys())
    
    valid_minute_days = 0
    total_days = len(sorted_dates)
    
    for d in sorted_dates:
        counts = date_counts[d]
        avg_rows = np.mean(counts)
        min_rows = np.min(counts)
        max_rows = np.max(counts)
        
        # Verdict
        if avg_rows > 300:
            verdict = "FULL (Minute)"
            valid_minute_days += 1
        elif avg_rows > 10:
            verdict = "PARTIAL"
        else:
            verdict = "DAILY/SPARSE"
            
        print(f"{str(d):<12} | {avg_rows:>10.1f} | {min_rows:>10} | {max_rows:>10} | {verdict}")

    print("-" * 65)
    print(f"Total Days Found: {total_days}")
    print(f"Effective Minute Data Days (>300 rows): {valid_minute_days}")
    
    range_msg = "Unknown"
    if valid_minute_days > 0:
        # Find continuous range?
        pass

if __name__ == "__main__":
    analyze_fidelity()
