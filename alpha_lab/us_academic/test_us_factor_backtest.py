"""
Tests for US Factor Backtest Runner
"""

import unittest
from pathlib import Path
import sys
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.us_academic.us_factor_backtest import USFactorBacktestRunner
from config import PATHS

class TestUSFactorBacktest(unittest.TestCase):
    
    def setUp(self):
        self.runner = USFactorBacktestRunner()
        # Clean up experiments/us_factors for test
        self.exp_dir = PATHS.EXPERIMENTS_DIR / "us_factors"
        if self.exp_dir.exists():
            shutil.rmtree(self.exp_dir)

    def test_run_backtest_simulation(self):
        """Test that the backtest runs and produces output"""
        strategy = "TEST_STRATEGY"
        result = self.runner.run_backtest(strategy, "2020-01-01", "2021-01-01")
        
        # Check result structure
        self.assertEqual(result.name, strategy)
        self.assertIn("sharpe", result.metrics)
        self.assertIn("max_drawdown", result.metrics)
        
        # Check output files
        # Find the directory created (it has a timestamp)
        created_dirs = list(self.exp_dir.glob(f"{strategy}_*"))
        self.assertTrue(len(created_dirs) > 0)
        
        output_dir = created_dirs[0]
        self.assertTrue((output_dir / "metrics.csv").exists())
        self.assertTrue((output_dir / "equity.csv").exists())
        self.assertTrue((output_dir / "report.md").exists())

    def test_approval_logic(self):
        """Test approval rules"""
        # Case 1: Good metrics
        good_metrics = {
            "sharpe": 2.0,
            "max_drawdown": 0.1,
            "cagr": 0.2,
            "volatility": 0.1,
            "total_return": 0.2,
            "years": 1.0
        }
        approved, failed = self.runner._evaluate_strategy("US_MOM_12_1", good_metrics)
        self.assertTrue(approved)
        self.assertEqual(len(failed), 0)
        
        # Case 2: Bad metrics (Sharpe too low)
        bad_metrics = {
            "sharpe": 0.1,
            "max_drawdown": 0.1,
            "cagr": 0.01,
            "volatility": 0.1,
            "total_return": 0.01,
            "years": 1.0
        }
        approved, failed = self.runner._evaluate_strategy("US_MOM_12_1", bad_metrics)
        self.assertFalse(approved)
        self.assertTrue(any("Sharpe" in f for f in failed))

if __name__ == '__main__':
    unittest.main()
