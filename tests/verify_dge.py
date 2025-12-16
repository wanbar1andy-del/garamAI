
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.risk.dge import DailyGrowthEngine, RiskConfig, MarketRegime

def test_dge_logic():
    print("Testing Daily Growth Engine...")
    
    # 1. Setup Config
    config = RiskConfig(
        max_daily_loss_pct=0.03,
        max_risk_per_trade_pct=0.01, # 1% risk
        max_position_size_pct=0.50,  # 50% max size
        use_kelly=True,
        kelly_fraction=0.5           # Half Kelly
    )
    
    engine = DailyGrowthEngine(config)
    capital = 100000.0 # $100k
    
    # 2. Test Risk-Based Sizing (No Kelly Stats)
    # Entry: 100, SL: 95 (5% risk)
    # Risk Amount = 100k * 1% = 1000
    # Position Size = 1000 / 0.05 = 20,000
    print("\n[Test 1] Risk-Based Sizing")
    size_risk = engine.calculate_position_size(capital, 100.0, 95.0)
    print(f"Expected: 20000.0, Got: {size_risk}")
    assert abs(size_risk - 20000.0) < 1.0
    
    # 3. Test Kelly Sizing (Constraint)
    # Win Rate: 60%, Payoff: 2.0
    # Kelly f* = 0.6 - 0.4/2 = 0.6 - 0.2 = 0.4 (40%)
    # Half Kelly = 0.2 (20%)
    # Kelly Size = 100k * 0.2 = 20,000
    # Risk-Based Size (same as above) = 20,000
    # So result should be 20,000
    print("\n[Test 2] Kelly Sizing (Equal)")
    stats = {'win_rate': 0.6, 'payoff_ratio': 2.0}
    size_kelly = engine.calculate_position_size(capital, 100.0, 95.0, stats)
    print(f"Expected: 20000.0, Got: {size_kelly}")
    assert abs(size_kelly - 20000.0) < 1.0
    
    # 4. Test Kelly Sizing (Limiting)
    # Win Rate: 55%, Payoff: 1.0
    # Kelly f* = 0.55 - 0.45/1 = 0.10 (10%)
    # Half Kelly = 0.05 (5%)
    # Kelly Size = 100k * 0.05 = 5,000
    # Risk-Based Size = 20,000
    # Result should be min(20000, 5000) = 5000
    print("\n[Test 3] Kelly Sizing (Limiting)")
    stats_weak = {'win_rate': 0.55, 'payoff_ratio': 1.0}
    size_kelly_limit = engine.calculate_position_size(capital, 100.0, 95.0, stats_weak)
    print(f"Expected: 5000.0, Got: {size_kelly_limit}")
    assert abs(size_kelly_limit - 5000.0) < 1.0
    
    # 5. Test Regime Multiplier
    # Using Test 1 setup (20,000 base)
    # YELLOW regime -> 0.5 multiplier -> 10,000
    print("\n[Test 4] Regime Multiplier (YELLOW)")
    size_yellow = engine.calculate_position_size(capital, 100.0, 95.0, regime="YELLOW")
    print(f"Expected: 10000.0, Got: {size_yellow}")
    assert abs(size_yellow - 10000.0) < 1.0
    
    # RED regime -> 0.0 multiplier -> 0
    print("\n[Test 5] Regime Multiplier (RED)")
    size_red = engine.calculate_position_size(capital, 100.0, 95.0, regime="RED")
    print(f"Expected: 0.0, Got: {size_red}")
    assert size_red == 0.0
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_dge_logic()
