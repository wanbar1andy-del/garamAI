import unittest
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.monitoring.shadow_performance import ShadowPerformanceAggregator
from garam.config import PATHS

class TestShadowPerformance(unittest.TestCase):
    def setUp(self):
        self.test_date = "20990101"
        self.aggregator = ShadowPerformanceAggregator(date_str=self.test_date)
        
        # Create mock trades
        self.mock_trades = [
            # Trade 1: Buy 10 @ 10000, Sell 10 @ 11000 (+10000 gross)
            {"timestamp": "2099-01-01T09:00:00", "symbol": "005930", "action": "BUY", "qty": 10, "price": 10000},
            {"timestamp": "2099-01-01T09:10:00", "symbol": "005930", "action": "SELL", "qty": 10, "price": 11000},
            
            # Trade 2: Buy 10 @ 10000, Sell 10 @ 9000 (-10000 gross)
            {"timestamp": "2099-01-01T10:00:00", "symbol": "000660", "action": "BUY", "qty": 10, "price": 10000},
            {"timestamp": "2099-01-01T10:10:00", "symbol": "000660", "action": "SELL", "qty": 10, "price": 9000}
        ]
        
        # Save mock trades
        with open(self.aggregator.trades_file, 'w', encoding='utf-8') as f:
            json.dump(self.mock_trades, f)
            
    def tearDown(self):
        # Cleanup
        if self.aggregator.trades_file.exists():
            os.remove(self.aggregator.trades_file)
        if self.aggregator.output_json.exists():
            os.remove(self.aggregator.output_json)
        if self.aggregator.output_md.exists():
            os.remove(self.aggregator.output_md)

    def test_calculate_metrics(self):
        metrics = self.aggregator.calculate_metrics(self.mock_trades)
        
        self.assertEqual(metrics['total_trades'], 4)
        self.assertEqual(metrics['completed_trades'], 2)
        self.assertEqual(metrics['winning_trades'], 1)
        self.assertEqual(metrics['losing_trades'], 1)
        self.assertEqual(metrics['win_rate'], 50.0)
        
        # P&L Check
        # Trade 1: (11000 - 10000) * 10 = 10000
        # Cost 1: (10000*10*0.0023) + ((10000+11000)*10*0.00015) = 230 + 31.5 = 261.5
        # Net 1: 9738.5
        
        # Trade 2: (9000 - 10000) * 10 = -10000
        # Cost 2: (10000*10*0.0023) + ((10000+9000)*10*0.00015) = 230 + 28.5 = 258.5
        # Net 2: -10258.5
        
        # Total: -520
        
        expected_pnl = 9738.5 - 10258.5
        self.assertAlmostEqual(metrics['total_pnl'], round(expected_pnl, 0), delta=5)

    def test_generate_report(self):
        metrics = self.aggregator.generate_report()
        self.assertTrue(self.aggregator.output_json.exists())
        self.assertTrue(self.aggregator.output_md.exists())
        
        with open(self.aggregator.output_json, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['date'], self.test_date)

if __name__ == '__main__':
    unittest.main()
