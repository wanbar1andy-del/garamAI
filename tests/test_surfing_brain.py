import unittest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from garam.live.surfing_brain_adapter import SurfingBrainAdapter

class TestSurfingBrain(unittest.TestCase):
    def setUp(self):
        self.brain = SurfingBrainAdapter()
        
    def test_trend_following_buy(self):
        # Golden Cross + Price above MA
        features = {
            'close': 105,
            'ma_fast': 100,
            'ma_slow': 90,
            'open': 100
        }
        signal = self.brain.decide(features)
        self.assertEqual(signal, 1) # BUY
        
    def test_trend_following_sell(self):
        # Dead Cross
        features = {
            'close': 95,
            'ma_fast': 90,
            'ma_slow': 100,
            'open': 98
        }
        signal = self.brain.decide(features)
        self.assertEqual(signal, -1) # SELL
        
    def test_trend_following_exit(self):
        # Uptrend but price drops below MA
        features = {
            'close': 98,
            'ma_fast': 100,
            'ma_slow': 90,
            'open': 99
        }
        signal = self.brain.decide(features)
        self.assertEqual(signal, -1) # SELL (Exit)
        
    def test_rsi_oversold(self):
        features = {
            'close': 100,
            'rsi': 25,
            'ma_fast': 100,
            'ma_slow': 100
        }
        signal = self.brain.decide(features)
        self.assertEqual(signal, 1) # BUY
        
    def test_rsi_overbought(self):
        features = {
            'close': 100,
            'rsi': 75,
            'ma_fast': 100,
            'ma_slow': 100
        }
        signal = self.brain.decide(features)
        self.assertEqual(signal, -1) # SELL

if __name__ == '__main__':
    unittest.main()
