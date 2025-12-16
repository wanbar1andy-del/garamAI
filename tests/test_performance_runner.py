"""
Test Performance Runner
Verifies that the performance runner script works correctly.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.run_kr_intraday_performance import PerformanceRunner

class TestPerformanceRunner(unittest.TestCase):
    @patch('scripts.run_kr_intraday_performance.KRMinuteLoader')
    @patch('scripts.run_kr_intraday_performance.IntradayBacktestRunner')
    def test_run_end_to_end(self, MockBacktestRunner, MockLoader):
        # Initialize runner inside patched context
        runner = PerformanceRunner(top_n=2)
        # Mock Loader
        mock_loader_instance = MockLoader.return_value
        # Create dummy data
        dates = pd.date_range(start="2025-11-01", periods=10, freq="1min")
        df = pd.DataFrame({
            'open': [100]*10, 'high': [101]*10, 'low': [99]*10, 'close': [100]*10, 'volume': [1000]*10
        }, index=dates)
        mock_loader_instance.load.return_value = df
        
        # Mock BacktestRunner
        mock_runner_instance = MockBacktestRunner.return_value
        mock_runner_instance.run.return_value = {
            "symbol": "005930",
            "metrics": {"total_pnl": 1000}
        }
        # Mock strategy account history for PnL extraction
        mock_strategy = MagicMock()
        mock_runner_instance.strategy = mock_strategy
        # Mock equity history
        EquityPoint = MagicMock()
        ep1 = MagicMock()
        ep1.timestamp = datetime(2025, 11, 1)
        ep1.pnl_balance = 0
        ep2 = MagicMock()
        ep2.timestamp = datetime(2025, 11, 2)
        ep2.pnl_balance = 1000
        
        # We need to attach this to the strategy instance that is created inside run()
        # Since run() creates new instances, we need to mock the strategy class or the runner's strategy access
        # But in our script, we access `strategy.account.equity_history`
        # We can mock the strategy class instantiation in the runner
        
        # Actually, let's just run the script and mock the internal calls
        # The script instantiates strategies from `self.strategies`
        
        # Let's mock the strategy classes in `self.strategies`
        MockStrategy = MagicMock()
        MockStrategy.return_value.account.equity_history = [ep1, ep2]
        runner.strategies = {"TEST_STRAT": MockStrategy}
        
        # Run
        runner.run("2025-11-01", "2025-11-02", ["TEST_STRAT"])
        
        # Verify
        self.assertTrue(mock_loader_instance.load.called)
        self.assertTrue(mock_runner_instance.run.called)

if __name__ == '__main__':
    unittest.main()
