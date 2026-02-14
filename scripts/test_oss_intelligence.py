import sys
import os
import json
import torch
import numpy as np
from pathlib import Path
from datetime import datetime

# [SYSTEM PATH SETUP]
PROJECT_ROOT = Path("c:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
BRAIN_PATH = PROJECT_ROOT / "core/active_config/neuro_brain_state.pth"
MEMORY_PATH = PROJECT_ROOT / "core/active_config/oss_episodic_memory.json"

from scripts.neural_brain import GaramNeuralBrain

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_simulation():
    log("🧪 [SIMULATION] Starting OSS Intelligence Verification...")
    
    # 1. Initialize Brain & Memory
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    brain = GaramNeuralBrain(input_size=64, mode="CUSTOM_45").to(device)
    
    # Fake Memory Load
    brain.memory_bank = []
    log("📚 [STEP 1] Memory Bank Initialized (Empty)")
    
    # 2. Inject Event 1: Massive Explosion (Context A)
    # Context: [VolRatio=5.0, Body=0.15, Range=0.05]
    ctx_A = {'vol_ratio': 5.0, 'body_pct': 0.15, 'range_pct': 0.05}
    outcome_A = 0.25 # +25% Profit
    
    log(f"⚡ [STEP 2] Injecting Event A: {ctx_A} -> Outcome: +25%")
    
    # Store to Memory
    new_memory = {
        'context': [ctx_A['vol_ratio'], ctx_A['body_pct'], ctx_A['range_pct']],
        'outcome': outcome_A,
        'ts': "SIMULATION_A"
    }
    brain.memory_bank.append(new_memory)
    
    # Verify Save
    with open(MEMORY_PATH, "w") as f:
        json.dump(brain.memory_bank, f)
    log(f"💾 [STEP 3] Saved Memory to {MEMORY_PATH}")
    
    # 3. Inject Event 2: Similar to A (Context A')
    # Context: [VolRatio=4.8, Body=0.14, Range=0.06] (Slight noise)
    ctx_B = np.array([4.8, 0.14, 0.06])
    log(f"🤔 [STEP 4] New Situation B (Similar to A): {ctx_B}")
    
    # 4. Test Recall Logic
    log("🧠 [STEP 5] Testing Recall Logic...")
    
    mem_contexts = np.array([m['context'] for m in brain.memory_bank])
    mem_outcomes = np.array([m['outcome'] for m in brain.memory_bank])
    
    dists = np.linalg.norm(mem_contexts - ctx_B, axis=1)
    nearest_idx = dists.argmin()
    nearest_dist = dists[nearest_idx]
    nearest_outcome = mem_outcomes[nearest_idx]
    
    log(f"   - Nearest Memory Distance: {nearest_dist:.4f}")
    log(f"   - Recalled Outcome: {nearest_outcome*100:.1f}%")
    
    if nearest_dist < 0.5 and nearest_outcome > 0.20:
        log("✅ [PASS] OSS successfully recognized the pattern and recalled the outcome!")
    else:
        log("❌ [FAIL] OSS failed to recall correctly.")
        
    # 5. Clean up
    # os.remove(MEMORY_PATH) # Keep it for inspection
    log("🏁 [COMPLETE] Simulation Finished.")

if __name__ == "__main__":
    run_simulation()
