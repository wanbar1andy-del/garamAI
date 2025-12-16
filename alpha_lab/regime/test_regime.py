"""
Tests for Market Regime Detection
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.regime.market_regime import MarketRegimeDetector, MarketState

class TestMarketRegime(unittest.TestCase):
    
    def setUp(self):
        self.detector = MarketRegimeDetector()
        
    def generate_synthetic_data(self, n=500, trend_type='up', vol_type='low'):
        """Generate synthetic OHLC data"""
        dates = pd.date_range('2023-01-01', periods=n, freq='D')
        
        # Base trend
        if trend_type == 'up':
            trend = np.linspace(100, 150, n)
        elif trend_type == 'down':
            trend = np.linspace(150, 100, n)
        else: # flat
            trend = np.linspace(100, 100, n)
            
        # Volatility
        if vol_type == 'high':
            noise = np.random.randn(n) * 2.0
        else: # low
            noise = np.random.randn(n) * 0.5
            
        close = trend + noise
        
        # Create OHLC
        df = pd.DataFrame(index=dates)
        df['close'] = close
        df['open'] = close + np.random.randn(n) * 0.1
        df['high'] = close + np.abs(np.random.randn(n) * 0.2)
        df['low'] = close - np.abs(np.random.randn(n) * 0.2)
        
        return df
        
    def test_initialization(self):
        """Test detector initialization"""
        self.assertEqual(self.detector.window_slow, 200)
        self.assertEqual(self.detector.window_fast, 50)
        
    def test_green_regime(self):
        """Test GREEN regime detection (Uptrend + Low Vol)"""
        # Generate long uptrend with low vol
        df = self.generate_synthetic_data(n=400, trend_type='up', vol_type='low')
        
        # Ensure price is above MA200 (simple check)
        # We need enough data for MA200 and ATR rank (252)
        
        result = self.detector.compute_regime(df['close'], df['high'], df['low'], df['close'])
        
        # Check last few rows
        last_state = result['state'].iloc[-1]
        
        # Note: Synthetic data might not perfectly align with "low vol" percentile 
        # because percentile is relative to history. 
        # But generally, steady uptrend should be GREEN or YELLOW.
        # Ideally GREEN if vol is consistently low.
        
        print(f"\n[Test Green] Last State: {last_state}")
        print(f"MA Dist: {result['ma_dist'].iloc[-1]:.4f}")
        print(f"ATR Pct: {result['atr_pct'].iloc[-1]:.4f}")
        
        # We accept GREEN or YELLOW (if vol percentile isn't low enough yet)
        self.assertIn(last_state, [MarketState.GREEN.value, MarketState.YELLOW.value])
        
    def test_red_regime(self):
        """Test RED regime detection (Downtrend + High Vol)"""
        # Generate downtrend with high vol
        df = self.generate_synthetic_data(n=400, trend_type='down', vol_type='high')
        
        result = self.detector.compute_regime(df['close'], df['high'], df['low'], df['close'])
        last_state = result['state'].iloc[-1]
        
        print(f"\n[Test Red] Last State: {last_state}")
        print(f"MA Dist: {result['ma_dist'].iloc[-1]:.4f}")
        print(f"ATR Pct: {result['atr_pct'].iloc[-1]:.4f}")
        
        # Should be RED or YELLOW
        self.assertIn(last_state, [MarketState.RED.value, MarketState.YELLOW.value])
        
    def test_get_current_state(self):
        """Test single state retrieval"""
        df = self.generate_synthetic_data(n=400)
        metrics = self.detector.get_current_state(df['close'], df['high'], df['low'], df['close'])
        
        self.assertIsNotNone(metrics)
        self.assertIsInstance(metrics.state, MarketState)
        self.assertIsInstance(metrics.trend_score, float)
        
    def test_insufficient_data(self):
        """Test handling of insufficient data"""
        df = self.generate_synthetic_data(n=50) # Less than 200
        result = self.detector.compute_regime(df['close'], df['high'], df['low'], df['close'])
        
        # Should be all None or NaN for state
        self.assertTrue(pd.isna(result['state'].iloc[-1]))

if __name__ == '__main__':
    unittest.main()
