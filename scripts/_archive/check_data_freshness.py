
import os
import glob
from datetime import datetime
import pandas as pd

def check_freshness(directory):
    print(f"Checking directory: {directory}")
    files = glob.glob(os.path.join(directory, "*_1m.csv"))
    print(f"Found {len(files)} files.")
    
    file_dates = []
    for f in files:
        mtime = os.path.getmtime(f)
        dt = datetime.fromtimestamp(mtime)
        file_dates.append({'file': os.path.basename(f), 'mtime': dt, 'path': f})
        
    df = pd.DataFrame(file_dates)
    if df.empty:
        print("No files found.")
        return

    # Find the most common date (mode)
    df['date_str'] = df['mtime'].dt.strftime('%Y-%m-%d')
    mode_date = df['date_str'].mode()[0]
    print(f"Most common date: {mode_date}")
    
    # Find files that are NOT from the mode date
    stale_files = df[df['date_str'] != mode_date]
    
    if not stale_files.empty:
        print(f"\nFound {len(stale_files)} stale files (not {mode_date}):")
        for _, row in stale_files.iterrows():
            print(f"{row['file']} - {row['mtime']}")
    else:
        print("\nAll files are up to date.")

if __name__ == "__main__":
    target_dir = r"g:\내 드라이브\garamdata\history\minute"
    check_freshness(target_dir)
