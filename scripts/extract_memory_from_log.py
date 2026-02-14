import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("c:/garam/garam")
LOG_FILE = PROJECT_ROOT / "logs/oss_wisdom_bridge.log"
MEMORY_PATH = PROJECT_ROOT / "core/active_config/oss_episodic_memory.json"

def run_extraction():
    print("🔍 [MEMORY EXTRACTION] Mining log for golden memories...")
    
    if not LOG_FILE.exists():
        print("❌ Log file not found.")
        return
        
    memories = []
    
    # Enhanced Regex to capture Context & Outcome
    # Pattern 1: Event Detection -> Look for Context
    # Since previous logs didn't output full context vector, we will construct synthetic context based on event type.
    # Event: EXPLOSION -> High Vol, High Body
    # Event: SQUEEZE -> Low Vol, Low Range
    
    # Phase 3 Log Pattern:
    # [23:10:58] 🥀 MOMENTUM DECAY: 214370 | Score 12.0 -> 9.0 | PnL: -5.60%
    # [23:10:29] 🚨 HERO FORCE ATTACK! 034020 (Impact: 0.0%)
    
    # We will look for trade exits with distinct PnL to seed memory
    # [23:10:59] OSS Trade Exit: 001430 | [OK] PROFIT (2.80%)
    
    # Let's parse the file line by line
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    count = 0
    for line in lines:
        # [Strategy 1] PnL Mining
        # Look for: "PnL: 2.80%" or "PROFIT (2.80%)"
        if "PnL:" in line or "PROFIT" in line or "LOSS" in line:
            # Extract PnL percentage
            match = re.search(r"([\+\-]?\d+\.\d+)%", line)
            if match:
                pnl = float(match.group(1))
                
                # Synthetic Context Generation based on PnL
                # If Big Win (>5%), assume Energy Explosion context
                # If Small Win (1-3%), assume Trend context
                # If Loss (<-3%), assume Trap context
                
                context = [0.0, 0.0, 0.0]
                event_type = "UNKNOWN"
                
                if pnl > 5.0:
                    event_type = "ENERGY_EXPLOSION"
                    context = [5.0, 0.10, 0.05] # High Vol, Big Body
                elif pnl > 2.0:
                    event_type = "TREND_FOLLOW"
                    context = [2.0, 0.03, 0.02] # Mid Vol, Mid Body
                elif pnl < -3.0: # Big Loss
                    event_type = "TRAP"
                    context = [4.0, -0.05, 0.08] # High Vol, Drop
                
                if event_type != "UNKNOWN":
                    # Create Memory Entry
                    # We just use current time as placeholder timestamp
                    mem_entry = {
                        'context': context,
                        'outcome': pnl / 100.0, # Convert % to decimal
                        'ts': "RECOVERED_MEMORY"
                    }
                    memories.append(mem_entry)
                    count += 1
                    
    print(f"✅ Extracted {count} memory seeds from logs.")
    
    # Load existing if any
    if MEMORY_PATH.exists():
        try:
            with open(MEMORY_PATH, "r") as f:
                existing = json.load(f)
                memories.extend(existing)
        except:
            pass
            
    # Save Combined
    # Deduplicate? No, more data is better for weighting.
    with open(MEMORY_PATH, "w") as f:
        json.dump(memories, f, indent=4)
        
    print(f"💾 Saved {len(memories)} total episodes to {MEMORY_PATH}")

if __name__ == "__main__":
    run_extraction()
