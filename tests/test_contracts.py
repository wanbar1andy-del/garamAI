import unittest
import sys
from pathlib import Path
import pandas as pd

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.risk.portfolio_manager import PortfolioManager
from garam.risk.dge import DailyGrowthEngine, RiskConfig

class TestContracts(unittest.TestCase):
    
    def test_dge_interface(self):
        """
        Contract: DailyGrowthEngine.calculate_position_size
        Input: capital, price, stop_loss_price, strategy_stats, regime
        Output: position_size_krw (float)
        """
        config = RiskConfig(max_risk_per_trade_pct=0.01)
        engine = DailyGrowthEngine(config)
        
        # Mock Inputs
        capital = 100_000_000
        price = 10000
        stop_loss = 9500 # 5% risk
        stats = {'win_rate': 0.5, 'avg_win': 0.02, 'avg_loss': 0.01}
        
        # Call
        size = engine.calculate_position_size(capital, price, stop_loss, stats, 'GREEN')
        
        # Assertions
        self.assertIsInstance(size, float, "Output must be float")
        self.assertGreaterEqual(size, 0, "Size must be non-negative")
        self.assertLessEqual(size, capital, "Size cannot exceed capital")
        
        # Risk Check: 100M * 1% = 1M risk. 
        # Loss per share = 500. 
        # Max Qty = 1M / 500 = 2000. 
        # Max Size = 2000 * 10000 = 20M.
        self.assertLessEqual(size, 20_000_000 * 1.01, "Size exceeds risk limit")

    def test_pm_interface(self):
        """
        Contract: PortfolioManager.calculate_position_size
        Input: symbol, price, stop_loss_price, regime, market_data, sector_data
        Output: adjusted_size_krw (float)
        """
        pm = PortfolioManager(100_000_000)
        config = RiskConfig()
        pm.register_symbol("005930", config)
        
        # Mock Inputs
        price = 70000
        sl = 68000
        
        # Call
        size = pm.calculate_position_size("005930", price, sl, 'GREEN')
        
        # Assertions
        self.assertIsInstance(size, float)
        self.assertGreaterEqual(size, 0)
        
        # HeatScore Contract
        # If HeatScore is updated, size should change (within limits)
        pm.update_heat_score(2.0) # Max Bull
        size_bull = pm.calculate_position_size("005930", price, sl, 'GREEN')
        
        pm.update_heat_score(-2.0) # Max Bear
        size_bear = pm.calculate_position_size("005930", price, sl, 'GREEN')
        
        self.assertGreaterEqual(size_bull, size_bear, "Bullish size should be >= Bearish size")

    def test_heatscore_range(self):
        """
        Contract: HeatScore must be clamped between -2.0 and +2.0
        """
        pm = PortfolioManager(100_000_000)
        
        pm.update_heat_score(5.0)
        self.assertEqual(pm.heat_score, 2.0, "HeatScore should be clamped to max 2.0")
        
        pm.update_heat_score(-5.0)
        self.assertEqual(pm.heat_score, -2.0, "HeatScore should be clamped to min -2.0")

if __name__ == "__main__":
    unittest.main()
