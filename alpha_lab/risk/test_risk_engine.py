"""
Tests for Risk Engine (Exit & Position Sizing)
"""

import sys
from pathlib import Path
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.risk.exit_engine import ExitEngine, ExitType
from alpha_lab.risk.position_sizer import PositionSizer
from alpha_lab.regime.market_regime import MarketState

class TestRiskEngine(unittest.TestCase):
    
    def setUp(self):
        self.exit_engine = ExitEngine()
        self.sizer = PositionSizer()
        
    def test_exit_calculation_green(self):
        """Test exit levels in GREEN regime (Wide stops)"""
        entry = 100.0
        atr = 2.0
        regime = MarketState.GREEN
        
        params = self.exit_engine.calculate_initial_levels(entry, atr, regime, direction='long')
        
        # Green Stop = 2.0 ATR
        expected_stop = 100.0 - (2.0 * 2.0) # 96.0
        # Green Target = 3.0 R (Risk = 4.0) -> Reward = 12.0
        expected_target = 100.0 + (4.0 * 3.0) # 112.0
        
        self.assertEqual(params.stop_price, expected_stop)
        self.assertEqual(params.target_price, expected_target)
        
    def test_exit_calculation_yellow(self):
        """Test exit levels in YELLOW regime (Tight stops)"""
        entry = 100.0
        atr = 2.0
        regime = MarketState.YELLOW
        
        params = self.exit_engine.calculate_initial_levels(entry, atr, regime, direction='long')
        
        # Yellow Stop = 1.5 ATR
        expected_stop = 100.0 - (2.0 * 1.5) # 97.0
        
        self.assertEqual(params.stop_price, expected_stop)
        
    def test_trailing_stop_update(self):
        """Test trailing stop ratchet logic"""
        entry = 100.0
        current_stop = 96.0
        atr = 2.0
        regime = MarketState.GREEN
        
        # Price moves up to 105
        # New stop should be 105 - (2.0 * 2.0) = 101
        new_stop = self.exit_engine.update_trailing_stop(105.0, current_stop, atr, regime, direction='long')
        self.assertEqual(new_stop, 101.0)
        
        # Price drops to 103
        # New calculated stop would be 103 - 4 = 99
        # But ratchet should keep it at 101
        next_stop = self.exit_engine.update_trailing_stop(103.0, new_stop, atr, regime, direction='long')
        self.assertEqual(next_stop, 101.0)
        
    def test_position_sizing_green(self):
        """Test sizing in GREEN regime (Full size)"""
        equity = 100000.0
        risk_pct = 0.01 # 1% risk = 1000
        entry = 100.0
        stop = 90.0 # Risk per share = 10
        
        # Base Qty = 1000 / 10 = 100
        # Green Multiplier = 1.0 -> 100
        qty = self.sizer.calculate_quantity(equity, risk_pct, entry, stop, MarketState.GREEN)
        self.assertEqual(qty, 100)
        
    def test_position_sizing_yellow(self):
        """Test sizing in YELLOW regime (Half size)"""
        equity = 100000.0
        risk_pct = 0.01
        entry = 100.0
        stop = 90.0
        
        # Base Qty = 100
        # Yellow Multiplier = 0.5 -> 50
        qty = self.sizer.calculate_quantity(equity, risk_pct, entry, stop, MarketState.YELLOW)
        self.assertEqual(qty, 50)
        
    def test_position_sizing_red(self):
        """Test sizing in RED regime (Zero size)"""
        equity = 100000.0
        risk_pct = 0.01
        entry = 100.0
        stop = 90.0
        
        # Red Multiplier = 0.0 -> 0
        qty = self.sizer.calculate_quantity(equity, risk_pct, entry, stop, MarketState.RED)
        self.assertEqual(qty, 0)

if __name__ == '__main__':
    unittest.main()
