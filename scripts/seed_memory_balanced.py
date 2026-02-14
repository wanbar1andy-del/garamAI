import sys, os, json, random
import pandas as pd, numpy as np
from pathlib import Path

PROJECT_ROOT = Path("c:/garam/garam")
MEMORY_PATH = PROJECT_ROOT / "core/active_config/oss_episodic_memory.json"
CACHE_FILE = PROJECT_ROOT / "cache/market_matrix_8m.pkl"

def run():
    print("💎 [BALANCED HARVEST] Positive + Negative memories...")
    
    if MEMORY_PATH.exists():
        os.remove(MEMORY_PATH)
        print("🧹 Old memory wiped.")
    
    data = pd.read_pickle(CACHE_FILE)
    closes = data['closes']
    vols = data['volumes']
    
    all_syms = list(closes.columns)
    print(f"🔍 Scanning ALL {len(all_syms)} symbols...")
    
    pos_memories = []  # outcome > 0
    neg_memories = []  # outcome <= 0
    
    for sym in all_syms:
        try:
            c = closes[sym].dropna()
            v = vols[sym].dropna()
            if len(c) < 200: continue
            
            ret = c.pct_change()
            vol_ma = v.rolling(20).mean()
            vol_ratio = v / (vol_ma + 1e-9)
            
            for i in range(20, len(c)-60, 120):
                vr = vol_ratio.iloc[i]
                r = ret.iloc[i]
                if np.isnan(vr) or np.isinf(vr): vr = 0.0
                if np.isnan(r) or np.isinf(r): r = 0.0
                
                curr_px = c.iloc[i]
                next_px = c.iloc[i+60]
                outcome = (next_px - curr_px) / curr_px
                
                if abs(outcome) > 0.5: continue
                
                entry = {
                    'context': [float(vr), float(r), float(abs(r))],
                    'outcome': float(outcome),
                    'ts': str(c.index[i])
                }
                
                if outcome > 0:
                    pos_memories.append(entry)
                else:
                    neg_memories.append(entry)
        except:
            continue
    
    print(f"   Raw: Positive={len(pos_memories)}, Negative={len(neg_memories)}")
    
    # BALANCED: Equal positive and negative
    min_count = min(len(pos_memories), len(neg_memories), 1000)
    random.shuffle(pos_memories)
    random.shuffle(neg_memories)
    
    balanced = pos_memories[:min_count] + neg_memories[:min_count]
    random.shuffle(balanced)
    
    with open(MEMORY_PATH, "w") as f:
        json.dump(balanced, f)
    
    outcomes = [m['outcome'] for m in balanced]
    print(f"✅ Balanced Memories: {len(balanced)}")
    print(f"   Pos: {sum(1 for o in outcomes if o>0)}, Neg: {sum(1 for o in outcomes if o<=0)}")
    print(f"   Mean: {np.mean(outcomes):.4f}, Range: {min(outcomes):.4f} ~ {max(outcomes):.4f}")

if __name__ == "__main__":
    run()
