import pandas as pd
import time
from pathlib import Path
import shutil
import random
import os
from datetime import datetime, timedelta

# Project Root
project_root = Path(__file__).resolve().parent.parent.parent
minutes_dir = project_root / "GARAM_Data" / "history" / "minute"
realtime_dir = project_root / "GARAM_Data" / "realtime"

# Cleanup
if realtime_dir.exists():
    shutil.rmtree(realtime_dir)
realtime_dir.mkdir(parents=True)

# Test Targets
# 010130: Missing Bars, 09:09 Entry Logic
# 001430: Normal
# 005930: Benchmark
targets = ["010130", "001430", "005930"]

print("Loading Daily Data for Targets...")
daily_data = {}
for sym in targets:
    p = minutes_dir / f"{sym}.csv"
    if p.exists():
        df = pd.read_csv(p)
        # Filter 2025-12-15 09:00 ~ 10:00
        df['str_ts'] = df['date'].astype(str)
        mask = df['str_ts'].str.startswith("2025121509") # 09:00~09:59
        daily_data[sym] = df[mask].reset_index(drop=True)
        print(f"Loaded {sym}: {len(daily_data[sym])} bars")
    else:
        print(f"Warning: {sym} not found!")

# Generate Mock market_status.csv for MA60 Checkpoint
print("Generating Mock MA60 Data (market_status.csv)...")
market_status_path = project_root / "GARAM_Data" / "market_status.csv"
with open(market_status_path, "w") as f:
    f.write("symbol,ma60,vol_ma_20\n")
    for sym in targets:
        if sym in daily_data and not daily_data[sym].empty:
            # Set MA60 slightly below first close to allow Entry (Trend OK)
            first_close = daily_data[sym].iloc[0]['close']
            mock_ma60 = first_close * 0.95
            f.write(f"{sym},{mock_ma60:.2f},10000\n")
            print(f"MA60 for {sym}: {mock_ma60:.2f}")

print("\nStarting Pre-flight Feeder (Speed 10x)...")
# Simulation Loop: 09:00 to 10:00
start_time = pd.Timestamp("2025-12-15 09:00:00")
end_time = pd.Timestamp("2025-12-15 10:00:00")
curr_sim_time = start_time

while curr_sim_time < end_time:
    # str match
    ts_str = curr_sim_time.strftime("%Y%m%d%H%M00")
    
    print(f"Time: {curr_sim_time.time()}", end='\r')
    
    for sym in targets:
        if sym not in daily_data: continue
        df = daily_data[sym]
        
        # Check if row exists
        row = df[df['str_ts'] == ts_str]
        if not row.empty:
            # Atomic Write Pattern: Write to .tmp -> Rename to .csv
            # This prevents partial reads by the Engine
            
            p = realtime_dir / f"{sym}.csv"
            tmp_p = realtime_dir / f"{sym}.tmp"
            
            data_line = f"{row.iloc[0]['date']},{row.iloc[0]['open']},{row.iloc[0]['high']},{row.iloc[0]['low']},{row.iloc[0]['close']},{row.iloc[0]['volume']}\n"
            
            # Read existing content if p exists (to simulate append)
            # Efficient simulation: Open in 'a', but since we need atomic update for the READER,
            # we must write FULL CONTENT to tmp then move?
            # Or is 'append' atomic on OS level?
            # Append is NOT atomic for the reader if reader scans file size.
            # But the User Request says: "Feeder는 반드시 sym.csv.tmp에 append -> flush+close -> rename"
            # If we rename tmp to csv, we replace the old csv. So we must copy old content to tmp first?
            # Or does 'rename' overwrite? Yes.
            # So: Read Old CSV -> Write to Tmp -> Append New Line -> Rename.
            
            existing_content = ""
            if p.exists():
                with open(p, "r") as f:
                    existing_content = f.read()
            
            with open(tmp_p, "w") as f:
                f.write(existing_content if existing_content else "date,open,high,low,close,volume\n")
                f.write(data_line)
                f.flush()
                os.fsync(f.fileno())
                
            # Atomic Move
            shutil.move(tmp_p, p)

                    
    # Next minute
    curr_sim_time += timedelta(minutes=1)
    time.sleep(0.1) # 0.1s real = 1 min sim (600x speed)

print("\nFeeder Finished.")
