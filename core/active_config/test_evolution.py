
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.active_config.tactical_genome import dna

print("=== [OSS EXPERIENCE] Storing & Reflecting ===")

# 1. Initial State
print(f"1. Current Guard Ratio: {dna.get('liquidity_guard_ratio')*100:.1f}%")

# 2. Store a Bad Experience (Simulation)
print("\n>>> SIMULATION: Storing 'TRAPPED' experience...")
dna.remember(
    context={"mkt_vol": 100000, "my_pos": 35000},
    action="EXIT_ATTEMPT",
    outcome={"result": "TRAPPED", "slippage": "5%"}
)

# 3. Reflect (Learn from History)
dna.reflect()

# 4. Result
print(f"\n2. Evolved Guard Ratio: {dna.get('liquidity_guard_ratio')*100:.1f}%")
