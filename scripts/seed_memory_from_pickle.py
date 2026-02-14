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

def run_seed_from_pickle():
    print("📦 [PICKLE MINING] extracting memories from centralized cache...")
    
    if not CACHE_FILE.exists():
        print(f"❌ Cache file not found: {CACHE_FILE}")
        return

    # 1. Load Pickle & Inspect Structure
    try:
        data = pd.read_pickle(CACHE_FILE)
        print(f"   [INFO] Cache Type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"   [INFO] Keys: {list(data.keys())}")
            # Expected: 'closes', 'volumes' (from previous error log)
            # Maybe 'close', 'volume'?
            
            closes = data.get('closes')
            if closes is None: closes = data.get('close')
            
            vols = data.get('volumes')
            if vols is None: vols = data.get('volume')
            
        else:
            print("   [WARN] Unexpected Structure (Not Dict)")
            return

        if closes is None or vols is None:
            print("❌ Critical Data Missing (Need Close & Volume)")
            return
            
    except Exception as e:
        print(f"❌ Pickle Load Error: {e}")
        return

    # 2. Target Period (Last 2 Months: Dec ~ Jan)
    # Using real data range
    print(f"   [INFO] Data Range: {closes.index[0]} ~ {closes.index[-1]}")
    
    start_dt = pd.Timestamp("2025-12-01")
    end_dt = pd.Timestamp("2026-01-31")
    
    if start_dt > closes.index[-1]:
        print("⚠️ Warning: Target period is in the future relative to data.")
        # Fallback to last month of available data
        end_dt = closes.index[-1]
        start_dt = end_dt - pd.Timedelta(days=30)
        print(f"   [ADJUST] New Range: {start_dt} ~ {end_dt}")

    # 3. Harvest Memories
    memories = []
    
    # Select Random 200 Symbols
    all_syms = list(closes.columns)
    random.shuffle(all_syms)
    target_syms = all_syms[:200]
    
    print(f"🔍 Scanning {len(target_syms)} symbols in {start_dt.date()}~{end_dt.date()}...")
    
    for sym in target_syms:
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
            
            # Scan every 60 mins (Hourly Snapshot)
            # UNCHAINED: Store diverse conditions, not just explosions
            
            for i in range(20, len(c)-60, 60):
                ts = c.index[i]
                
                vr = vol_ratio.iloc[i]
                r = ret.iloc[i]
                if np.isnan(vr) or np.isinf(vr): vr = 0.0
                if np.isnan(r) or np.isinf(r): r = 0.0
                
                # Context: [VolRatio, Return, Volatility_Proxy]
                # High/Low missing, so use abs(return) as proxy for range
                
                # Outcome: Next 60m return
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
                
        except:
            continue
            
    # 4. Save
    # Merge with existing 14 memories? Yes.
    existing = []
    if MEMORY_PATH.exists():
        try:
            with open(MEMORY_PATH, "r") as f:
                existing = json.load(f)
        except: pass
        
    print(f"   [MERGE] Existing {len(existing)} + New {len(memories)}")
    final_memories = existing + memories
    
    # Cap at 2000 oldest
    if len(final_memories) > 2000:
        final_memories = final_memories[-2000:]
        
    with open(MEMORY_PATH, "w") as f:
        json.dump(final_memories, f, indent=4)
        
    print(f"✅ Total Memories Stored: {len(final_memories)}")

if __name__ == "__main__":
    run_seed_from_pickle()
