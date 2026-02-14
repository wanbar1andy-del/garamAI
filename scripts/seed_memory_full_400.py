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
CACHE_FILE = PROJECT_ROOT / "cache/market_matrix_8m.pkl"

def run_seed_full_400():
    print("💎 [FULL HARVEST] Extracting memories from ALL 400+ SYMBOLS (Real Data)...")
    
    # 0. Clean old memory (Fake Purge)
    if MEMORY_PATH.exists():
        try:
            os.remove(MEMORY_PATH)
            print("🧹 Old memory wiped. Starting fresh.")
        except: pass
    
    if not CACHE_FILE.exists():
        print(f"❌ Cache file not found: {CACHE_FILE}")
        return

    # 1. Load Pickle
    try:
        data = pd.read_pickle(CACHE_FILE)
        closes = data.get('closes')
        vols = data.get('volumes')
        if closes is None: closes = data.get('close')
        if vols is None: vols = data.get('volume')

        if closes is None or vols is None:
            print("❌ Critical Data Missing")
            return
            
    except Exception as e:
        print(f"❌ Pickle Load Error: {e}")
        return

    # 2. Target Period (Last 2 Months)
    start_dt = pd.Timestamp("2025-12-01")
    end_dt = pd.Timestamp("2026-01-31")
    
    if start_dt > closes.index[-1]:
        end_dt = closes.index[-1]
        start_dt = end_dt - pd.Timedelta(days=60)
        print(f"   [ADJUST] New Range: {start_dt.date()} ~ {end_dt.date()}")

    # 3. Harvest Memories
    memories = []
    
    # Select ALL Symbols
    all_syms = list(closes.columns)
    print(f"🔍 Scanning ALL {len(all_syms)} symbols...")
    
    # Progress check
    total = len(all_syms)
    done = 0
    
    for sym in all_syms:
        try:
            # Slicing
            c = closes.loc[start_dt:end_dt][sym]
            v = vols.loc[start_dt:end_dt][sym]
            
            if len(c) < 120: continue
            
            # Features
            ret = c.pct_change()
            vol_ma = vols[sym].rolling(20).mean().loc[start_dt:end_dt]
            vol_ratio = v / (vol_ma + 1e-9)
            
            # Outcome Horizon: 60 mins
            # Taking 1 snapshot every 2 hours (120 mins) per symbol
            # To avoid memory overflow but cover everything
            
            for i in range(20, len(c)-60, 120):
                ts = c.index[i]
                
                vr = vol_ratio.iloc[i]
                r = ret.iloc[i]
                if np.isnan(vr) or np.isinf(vr): vr = 0.0
                if np.isnan(r) or np.isinf(r): r = 0.0
                
                curr_px = c.iloc[i]
                next_px = c.iloc[i+60]
                outcome = (next_px - curr_px) / curr_px
                
                if abs(outcome) > 0.5: continue # Outlier filter
                
                mem_entry = {
                    'context': [float(vr), float(r), float(abs(r))],
                    'outcome': float(outcome),
                    'ts': str(ts)
                }
                memories.append(mem_entry)
                
            done += 1
            if done % 50 == 0:
                print(f"   - Processed {done}/{total} symbols... ({len(memories)} memories)")
                
        except:
            continue
            
    # Cap at 5000 (Most Recent/Diverse)
    # Actually, keep all if reasonable size (<10MB)
    if len(memories) > 10000:
        print(f"   [TRIM] Keeping random 10000 out of {len(memories)}")
        random.shuffle(memories)
        memories = memories[:10000]
        
    # 4. Save
    with open(MEMORY_PATH, "w") as f:
        json.dump(memories, f, indent=4)
        
    print(f"✅ Total Memories Harvested: {len(memories)}")

if __name__ == "__main__":
    run_seed_full_400()
