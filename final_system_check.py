
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.active_config.tactical_genome import dna
from core.liquidity.physics_engine import LiquidityArchitect

print("=== [GARAM 2.1 FINAL CHECK] Philosophy Integration ===")

# 1. Intelligence (Wisdom DNA)
print("\n1. [Intelligence] Wisdom Check")
guard = dna.get("liquidity_guard_ratio")
print(f"   -> Current Liquidity Guard: {guard*100:.1f}% (Evolved Parameter)")

# 2. Physics Engine (Impact Calculation)
print("\n2. [Physics] Impact Simulation")
eng = LiquidityArchitect()
# Fitness Calculation Test
fitness = eng.calculate_fitness(profit=5000000, risk=100000, complexity=2) 
# Profit 5M, Risk 100k, Complexity 2 -> Score 25
print(f"   -> Evolutionary Fitness Score: {fitness:.2f} (Profit/Risk*Comp)")

res = eng.calculate_impact_power(100_000_000, 1_000_000_000, 0.04)
print(f"   -> Impact Power: {res['power_score']:.2f}% (Status: {res['status']})")

if res['status'] == "OPTIMAL":
    print("   ✅ SYSTEM OPERATIONAL. READY FOR DEPLOYMENT.")
else:
    print("   ⚠️ SYSTEM ALERT. INVESTIGATE.")
