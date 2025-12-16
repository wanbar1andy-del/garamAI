import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from garam.features.factory import FeatureFactory

class TestFeatureExpansion(unittest.TestCase):
    def setUp(self):
        self.factory = FeatureFactory()
        # Create mock data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='1min')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(100, 1000, 100)
        })
        
    def test_rsi(self):
        config = [{'name': 'rsi', 'params': {'period': 14}}]
        df_out = self.factory.compute_features(self.df, config)
        self.assertIn('rsi', df_out.columns)
        self.assertFalse(df_out['rsi'].isnull().all())
        # Check range
        self.assertTrue((df_out['rsi'].dropna() >= 0).all())
        self.assertTrue((df_out['rsi'].dropna() <= 100).all())
        
    def test_macd(self):
        config = [{'name': 'macd', 'params': {'fast': 12, 'slow': 26, 'signal': 9}}]
        df_out = self.factory.compute_features(self.df, config)
        self.assertIn('macd_line', df_out.columns)
        self.assertIn('macd_signal', df_out.columns)
        self.assertIn('macd_hist', df_out.columns)
        
    def test_bollinger(self):
        config = [{'name': 'bollinger', 'params': {'window': 20, 'num_std': 2.0}}]
        df_out = self.factory.compute_features(self.df, config)
        self.assertIn('bb_upper', df_out.columns)
        self.assertIn('bb_lower', df_out.columns)
        self.assertIn('bb_width', df_out.columns)
        self.assertIn('bb_pct_b', df_out.columns)

if __name__ == '__main__':
    unittest.main()
