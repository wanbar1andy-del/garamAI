"""
Tests for Surfing Brain
"""

import sys
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.brain.surfing_brain import SurfingBrain, MarketState

class TestSurfingBrain(unittest.TestCase):
    
    def setUp(self):
        self.brain = SurfingBrain()
        
    def generate_mock_data(self, n=300, trend='up'):
        """Generate mock price data for regime detection"""
        dates = pd.date_range('2023-01-01', periods=n, freq='D')
        if trend == 'up':
            prices = np.linspace(100, 150, n) + np.random.randn(n) * 0.5
        else:
            prices = np.linspace(150, 100, n) + np.random.randn(n) * 2.0
            
        return pd.Series(prices, index=dates)
        
    def test_assess_market(self):
        """Test market assessment updates state"""
        prices = self.generate_mock_data(trend='up')
        state = self.brain.assess_market(prices)
        
        self.assertIsNotNone(self.brain.current_regime_metrics)
        self.assertIn(state, [MarketState.GREEN, MarketState.YELLOW, MarketState.RED])
        
    def test_trade_instructions_green(self):
        """Test trade instructions in GREEN regime"""
        # Force brain state to GREEN
        prices = self.generate_mock_data(trend='up')
        self.brain.assess_market(prices)
        # Manually override to ensure test consistency
        if self.brain.current_regime_metrics:
             self.brain.current_regime_metrics.state = MarketState.GREEN
        
        instructions = self.brain.get_trade_instructions(
            symbol='TEST',
            entry_price=100.0,
            equity=100000.0,
            risk_pct=0.01,
            atr=2.0
        )
        
        self.assertEqual(instructions.action, 'BUY')
        self.assertEqual(instructions.regime, MarketState.GREEN)
        # Green: 2 ATR stop = 96.0
        self.assertEqual(instructions.stop_price, 96.0)
        # Green: Full size. Risk=1000, Risk/Share=4 -> Qty=250
        self.assertEqual(instructions.quantity, 250)
        
    def test_trade_instructions_red(self):
        """Test trade instructions in RED regime (Should block long)"""
        # Force brain state to RED
        prices = self.generate_mock_data(trend='down')
        self.brain.assess_market(prices)
        if self.brain.current_regime_metrics:
             self.brain.current_regime_metrics.state = MarketState.RED
             
        instructions = self.brain.get_trade_instructions(
            symbol='TEST',
            entry_price=100.0,
            equity=100000.0,
            risk_pct=0.01,
            atr=2.0,
            direction='long'
        )
        
        self.assertEqual(instructions.action, 'HOLD')
        self.assertEqual(instructions.quantity, 0)
        self.assertIn("RED Regime", instructions.reason)

    def test_should_trade(self):
        """Test strategy allowance logic"""
        # Mock state
        prices = self.generate_mock_data(trend='down')
        self.brain.assess_market(prices)
        if self.brain.current_regime_metrics:
             self.brain.current_regime_metrics.state = MarketState.RED
             
        # Momentum should be blocked in RED
        allowed = self.brain.should_trade('MOMENTUM')
        self.assertFalse(allowed)

if __name__ == '__main__':
    unittest.main()
