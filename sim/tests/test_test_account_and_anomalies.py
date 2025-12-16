"""
Tests for Test Trading Accounting
"""

import unittest
from datetime import datetime
import shutil
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sim.test_account import TestAccount, TradeExpectation, TradeOutcome
from config import PATHS

class TestTestAccount(unittest.TestCase):
    
    def setUp(self):
        self.account = TestAccount()
        self.strategy_id = "TEST_STRATEGY"
        self.run_id = "RUN_001"
        
        # Clean up experiments dir for test
        self.exp_dir = PATHS.EXPERIMENTS_DIR / self.strategy_id
        if self.exp_dir.exists():
            shutil.rmtree(self.exp_dir)

    def test_basic_accounting(self):
        """Test constant notional accounting"""
        # Initial state
        self.assertEqual(self.account.pnl_balance, 0.0)
        self.assertEqual(self.account.test_capital, 100_000_000)
        
        # Profitable trade
        self.account.on_trade_closed(1_000_000, datetime.now())
        self.assertEqual(self.account.pnl_balance, 1_000_000)
        self.assertEqual(self.account.test_capital, 100_000_000) # Should not change
        
        # Losing trade
        self.account.on_trade_closed(-500_000, datetime.now())
        self.assertEqual(self.account.pnl_balance, 500_000)
        
    def test_anomaly_detection(self):
        """Test anomaly detection logic"""
        exp = TradeExpectation(
            trade_id="T1",
            expected_direction="LONG",
            expected_R_range=(1.0, 3.0),
            expected_holding_period=5,
            expected_regime="EAT"
        )
        
        # Case 1: Underperformance (Realized R = -1.0, Expected Min = 1.0)
        # Threshold is min - 1.0 = 0.0. So -1.0 is anomaly.
        out_under = TradeOutcome(
            trade_id="T1",
            realized_R=-1.0,
            actual_holding_period=5,
            realized_pnl=-1000,
            regime_at_entry="EAT",
            regime_at_exit="EAT",
            max_favorable_excursion_R=0.5,
            max_adverse_excursion_R=-1.2
        )
        
        self.account.on_trade_closed(-1000, datetime.now(), exp, out_under)
        self.assertEqual(len(self.account.anomalies), 1)
        self.assertEqual(self.account.anomalies[0].anomaly_type, "UNDERPERFORM")
        
        # Case 2: Regime Drift
        out_drift = TradeOutcome(
            trade_id="T1",
            realized_R=1.5, # Normal R
            actual_holding_period=5,
            realized_pnl=1500,
            regime_at_entry="EAT",
            regime_at_exit="DEATH", # Drift
            max_favorable_excursion_R=2.0,
            max_adverse_excursion_R=-0.5
        )
        
        self.account.on_trade_closed(1500, datetime.now(), exp, out_drift)
        self.assertEqual(len(self.account.anomalies), 2)
        self.assertEqual(self.account.anomalies[1].anomaly_type, "REGIME_DRIFT")

    def test_file_outputs(self):
        """Test saving anomalies and summary"""
        exp = TradeExpectation("T1", "LONG", (1.0, 3.0), 5, "EAT")
        out = TradeOutcome("T1", -2.0, 5, -2000, "EAT", "EAT", 0, -2.0)
        
        self.account.on_trade_closed(-2000, datetime.now(), exp, out)
        
        self.account.save_anomalies(self.strategy_id, self.run_id)
        self.account.save_summary(self.strategy_id, self.run_id)
        
        # Check files
        jsonl_path = self.exp_dir / f"anomalies_{self.run_id}.jsonl"
        md_path = self.exp_dir / f"anomaly_summary_{self.run_id}.md"
        
        self.assertTrue(jsonl_path.exists())
        self.assertTrue(md_path.exists())
        
        # Verify JSONL content
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            line = f.readline()
            data = json.loads(line)
            self.assertEqual(data['type'], "UNDERPERFORM")

if __name__ == '__main__':
    unittest.main()
