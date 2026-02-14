import sys
import os
import json
import pandas as pd
import numpy as np
import random
from pathlib import Path

# [SYSTEM PATH SETUP]
PROJECT_ROOT = Path("c:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

MEMORY_PATH = PROJECT_ROOT / "core/active_config/oss_episodic_memory.json"
REAL_DATA_DIR = PROJECT_ROOT / "GARAM_Data/kr/intraday/1m"

def run_seed_december_harvest():
    print("🎄 [MEMORY HARVEST] Scanning December 2025 (Whole Month)...")
    
    if not REAL_DATA_DIR.exists():
        print(f"❌ Real Data Directory Not Found: {REAL_DATA_DIR}")
        return

    # 1. Target Period: Full Month
    start_dt = pd.Timestamp("2025-12-01")
    end_dt = pd.Timestamp("2025-12-31")
    
    memories = []
    files = list(REAL_DATA_DIR.glob("*.csv"))
    print(f"📂 Scanning {len(files)} symbol files...")
    
    # Shuffle files to get random samples from various symbols
    random.shuffle(files)
    
    count = 0
    target_count = 1000 # Aim for 1000 memories
    
    for f in files:
        if len(memories) >= target_count: break # Stop when enough
        if count > 300: break # Safety Break: max 300 files scanned
        
        try:
            # Read CSV
            df = pd.read_csv(f)
            df.columns = [c.lower() for c in df.columns]
            
            # Timestamp parsing
            if 'timestamp' in df.columns:
                df['dt'] = pd.to_datetime(df['timestamp'])
            elif 'date' in df.columns:
                 try:
                    df['dt'] = pd.to_datetime(df['date'])
                 except:
                    df['dt'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d%H%M%S', errors='coerce')
            
            if 'dt' not in df.columns: continue
            
            # Smart Filter before sorting (Speed up)
            # Find rows roughly in range
            # Check string matching first? No, slow.
            # Just parsing is fine.
            
            df = df.dropna(subset=['dt']).set_index('dt').sort_index()
            mask = (df.index >= start_dt) & (df.index <= end_dt)
            df_slice = df.loc[mask].copy()
            
            if len(df_slice) < 120: continue # Need at least 2 hours
            
            # 2. Extract RAW Context (Snapshots)
            
            df_slice['ret'] = df_slice['close'].pct_change()
            df_slice['range'] = (df_slice['high'] - df_slice['low']) / df_slice['low']
            df_slice['vol_ma'] = df_slice['volume'].rolling(20).mean()
            df_slice['vol_ratio'] = df_slice['volume'] / (df_slice['vol_ma'] + 1e-9)
            
            # Step size: 60 mins (Get 1 snapshot per hour per stock)
            # This gives ample variety
            for i in range(20, len(df_slice)-120, 60):
                row = df_slice.iloc[i]
                op = df_slice.iloc[i-1]['close']
                
                # Context Vector [VolRatio, Body, Range]
                vr = row['vol_ratio']
                if np.isnan(vr) or np.isinf(vr): vr = 0.0
                
                body = (row['close'] - op) / op
                rng = row['range']
                
                # Outcome (Next 120 mins Return)
                # Max Potential Upside/Downside could be used
                # But let's use Simple Close-to-Close Return (60m)
                
                next_px = df_slice['close'].iloc[i+60] if i+60 < len(df_slice) else df_slice['close'].iloc[-1]
                outcome = (next_px - row['close']) / row['close']
                
                # Filter out extreme outliers (bad data)
                if abs(outcome) > 0.5: continue 
                
                mem_entry = {
                    'context': [float(vr), float(body), float(rng)],
                    'outcome': float(outcome),
                    'ts': str(df_slice.index[i])
                }
                memories.append(mem_entry)
            
            count += 1
            if len(memories) % 100 == 0 and len(memories) > 0:
                print(f"   - Harvested {len(memories)} memories so far...")
            
        except Exception as e:
            continue
            
    # 3. Save
    print(f"💾 Saving {len(memories)} Harvested Memories to {MEMORY_PATH}")
    with open(MEMORY_PATH, "w") as f:
        json.dump(memories, f, indent=4)
        
    print("✅ Seed Injection Complete.")

if __name__ == "__main__":
    run_seed_december_harvest()
