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

def run_dec_w1_seeding():
    print("🎄 [MEMORY SEED] Injecting Dec W1 (2025-12-01~07) Events (UNCHAINED)...")
    
    if not REAL_DATA_DIR.exists():
        print(f"❌ Real Data Directory Not Found: {REAL_DATA_DIR}")
        return

    start_dt = pd.Timestamp("2025-12-01")
    end_dt = pd.Timestamp("2025-12-07")
    
    memories = []
    files = list(REAL_DATA_DIR.glob("*.csv"))
    print(f"📂 Scanning {len(files)} symbol files...")
    
    processed_files = 0
    
    for f in files:
        if processed_files > 50: break # Seed 50 symbols (Enough for context diversity)
        
        try:
            # Read CSV
            df = pd.read_csv(f)
            df.columns = [c.lower() for c in df.columns]
            
            # Timestamp parsing
            if 'timestamp' in df.columns:
                df['dt'] = pd.to_datetime(df['timestamp'])
            elif 'date' in df.columns:
                 # Try typical formats
                 try:
                    df['dt'] = pd.to_datetime(df['date'])
                 except:
                    df['dt'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d%H%M%S', errors='coerce')
            
            if 'dt' not in df.columns: continue
            
            df = df.dropna(subset=['dt']).set_index('dt').sort_index()
            
            # Filter Range
            mask = (df.index >= start_dt) & (df.index <= end_dt)
            df_slice = df.loc[mask].copy()
            
            if len(df_slice) < 60: continue
            
            # 2. Extract RAW Context (No Human Thresholds)
            # Just take snapshots of reality every 30 mins
            # This captures: Quiet times, Explosions, Trends, Chop... EVERYTHING.
            
            df_slice['ret'] = df_slice['close'].pct_change()
            df_slice['range'] = (df_slice['high'] - df_slice['low']) / df_slice['low']
            df_slice['vol_ma'] = df_slice['volume'].rolling(20).mean()
            df_slice['vol_ratio'] = df_slice['volume'] / (df_slice['vol_ma'] + 1e-9)
            
            # Step size: 30 (Every 30 mins)
            for i in range(20, len(df_slice)-120, 30):
                row = df_slice.iloc[i]
                op = df_slice.iloc[i-1]['close']
                
                # Context Vector
                vr = row['vol_ratio']
                body = (row['close'] - op) / op
                rng = row['range']
                
                # Outcome (Next 120 mins Return)
                future_h = df_slice['high'].iloc[i+1:i+120].max()
                future_l = df_slice['low'].iloc[i+1:i+120].min()
                entry_px = row['close']
                
                # Simple Outcome: Max Up - Max Down (Net Potential)
                # Or just Close-to-Close
                next_px = df_slice['close'].iloc[i+60] if i+60 < len(df_slice) else entry_px
                outcome = (next_px - entry_px) / entry_px
                
                mem_entry = {
                    'context': [float(vr), float(body), float(rng)],
                    'outcome': float(outcome),
                    'ts': str(df_slice.index[i])
                }
                memories.append(mem_entry)
            
            processed_files += 1
            
        except Exception as e:
            continue
            
    # 3. Save
    print(f"💾 Saving {len(memories)} Seed Memories to {MEMORY_PATH}")
    with open(MEMORY_PATH, "w") as f:
        json.dump(memories, f, indent=4)
        
    print("✅ Seed Injection Complete.")

if __name__ == "__main__":
    run_dec_w1_seeding()
