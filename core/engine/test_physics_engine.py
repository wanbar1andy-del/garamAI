
import sys
from pathlib import Path

# Fix import
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.liquidity.architect import LiquidityArchitect

arch = LiquidityArchitect()

print("\n" + "="*50)
print(" 🌪️ GARAM 2.1 IMPACT PHYSICS ENGINE TEST")
print("="*50)

# Scenario 1: Big Cap, Low Vol (Samsung Elec)
# Capital: 100M, ADV: 100B, Vol: 1.5%
res1 = arch.calculate_impact_power(capital=100_000_000, adv=100_000_000_000, volatility=0.015)
print(f"\n[Case 1] Big Cap (Samsung Elec)")
print(f"   Power: {res1['power_score']:.4f}% | Status: {res1['status']}")
print(f"   Strategy: {res1['slicing']}")

# Scenario 2: Small Cap (KOSDAQ Hero)
# Capital: 100M, ADV: 1B, Vol: 4%
res2 = arch.calculate_impact_power(capital=100_000_000, adv=1_000_000_000, volatility=0.04)
print(f"\n[Case 2] Small Cap (KOSDAQ Hero)")
print(f"   Power: {res2['power_score']:.4f}% | Status: {res2['status']}")
print(f"   Strategy: {res2['slicing']}")

# Scenario 3: Thin Market (Danger)
# Capital: 300M, ADV: 500M, Vol: 2%
res3 = arch.calculate_impact_power(capital=300_000_000, adv=500_000_000, volatility=0.02)
print(f"\n[Case 3] Thin Market (Illiquid)")
print(f"   Power: {res3['power_score']:.4f}% | Status: {res3['status']}")
print(f"   Strategy: {res3['slicing']}")

# Typhoon Probability
total_mkt_val = 15_000_000_000_000 # 15 Trillion (Bull Market)
prob = arch.calculate_typhoon_probability(total_mkt_val, 0)
print(f"\n[Market Context] Bull Market (15T)")
print(f"   Typhoon Attraction Probability: {prob:.1f}%")
