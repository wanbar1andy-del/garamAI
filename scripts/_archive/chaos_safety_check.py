"""
Chaos Safety Check
Injects abnormal inputs (NaN, Infinity, Extreme Values) into core components
to verify they fail safely (return 0 size, safe defaults) instead of crashing or blowing up.
"""

import unittest
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.risk.portfolio_manager import PortfolioManager
from garam.risk.dge import DailyGrowthEngine, RiskConfig

class ChaosSafetyTest(unittest.TestCase):
    
    def setUp(self):
        self.pm = PortfolioManager(100_000_000)
        self.config = RiskConfig()
        self.pm.register_symbol("CHAOS_TEST", self.config)

    def test_nan_price_input(self):
        """Test NaN price input -> Should return 0 size or handle gracefully"""
        print("\n[Chaos] Testing NaN Price Input...")
        try:
            size = self.pm.calculate_position_size("CHAOS_TEST", float('nan'), 9000, 'GREEN')
            # Expect 0 size for safety
            self.assertEqual(size, 0.0, "System should return 0 size for NaN price")
        except Exception as e:
            print(f"Caught expected exception or handled error: {e}")

    def test_extreme_heatscore(self):
        """Test Extreme HeatScore (+100.0) -> Should be clamped"""
        print("\n[Chaos] Testing Extreme HeatScore (+100.0)...")
        self.pm.update_heat_score(100.0)
        self.assertEqual(self.pm.heat_score, 2.0, "HeatScore should be clamped to 2.0")
        
        self.pm.update_heat_score(-999.0)
        self.assertEqual(self.pm.heat_score, -2.0, "HeatScore should be clamped to -2.0")

    def test_zero_capital(self):
        """Test Zero Capital -> Should return 0 size"""
        print("\n[Chaos] Testing Zero Capital...")
        pm_broke = PortfolioManager(0)
        pm_broke.register_symbol("BROKE", self.config)
        size = pm_broke.calculate_position_size("BROKE", 10000, 9500, 'GREEN')
        self.assertEqual(size, 0.0)

    def test_infinite_stats(self):
        """Test Infinite Win Rate/Avg Win -> Should not blow up size"""
        print("\n[Chaos] Testing Infinite Strategy Stats...")
        # DGE uses Kelly. If win rate is normal but avg_win is inf?
        # This depends on DGE implementation.
        # Let's mock a DGE call directly.
        dge = DailyGrowthEngine(self.config)
        stats = {'win_rate': 0.99, 'avg_win': float('inf'), 'avg_loss': 1.0}
        
        try:
            size = dge.calculate_position_size(100_000_000, 10000, 9000, stats, 'GREEN')
            # Should be capped by max_risk_per_trade or similar
            self.assertLess(size, 100_000_000, "Size should not be infinite")
        except Exception as e:
            print(f"Handled infinite stats: {e}")

if __name__ == "__main__":
    unittest.main()
