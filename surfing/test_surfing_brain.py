"""
Tests for Surfing Brain v1
"""

import unittest
from pathlib import Path
import sys
import shutil
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from surfing.surfing_brain import SurfingBrain, SurfingContext, Regime, Mode, SurfState
from config import PATHS

class TestSurfingBrain(unittest.TestCase):
    
    def setUp(self):
        # Clean up logs for test
        self.log_dir = PATHS.LOGS_DIR / "surfing_decisions"
        if self.log_dir.exists():
            shutil.rmtree(self.log_dir)
            
        self.brain = SurfingBrain()

    def test_mode_selection_shield(self):
        """Test SHIELD mode conditions"""
        # Case: DEATH regime
        ctx = SurfingContext(
            timestamp="2025-01-01",
            regime=Regime.DEATH,
            uncertainty=0.8, # High
            recent_expectancy_R=-0.1,
            recent_drawdown_pct=0.25 # Critical
        )
        decision = self.brain.evaluate(ctx)
        self.assertEqual(decision.mode, Mode.SHIELD)
        self.assertEqual(decision.risk_multiplier, 0.3) # From config

    def test_mode_selection_attack(self):
        """Test ATTACK mode conditions"""
        # Case: EAT regime, Low Uncertainty, Strong R
        ctx = SurfingContext(
            timestamp="2025-01-01",
            regime=Regime.EAT,
            uncertainty=0.2, # Low
            recent_expectancy_R=0.3, # Strong
            recent_drawdown_pct=0.0
        )
        decision = self.brain.evaluate(ctx)
        self.assertEqual(decision.mode, Mode.ATTACK)
        self.assertEqual(decision.risk_multiplier, 1.5)

    def test_mode_selection_cruise(self):
        """Test CRUISE mode (default)"""
        # Case: EAT regime but High Uncertainty -> Should not be ATTACK
        ctx = SurfingContext(
            timestamp="2025-01-01",
            regime=Regime.EAT,
            uncertainty=0.8, # High
            recent_expectancy_R=0.3,
            recent_drawdown_pct=0.0
        )
        decision = self.brain.evaluate(ctx)
        self.assertEqual(decision.mode, Mode.CRUISE)

    def test_surf_state(self):
        """Test Single vs Multi Model state"""
        # Low uncertainty -> Single
        ctx1 = SurfingContext("t1", Regime.EAT, 0.3, 0.1, 0.0)
        dec1 = self.brain.evaluate(ctx1)
        self.assertEqual(dec1.surf_state, SurfState.SINGLE_MODEL)
        
        # High uncertainty -> Multi
        ctx2 = SurfingContext("t2", Regime.EAT, 0.5, 0.1, 0.0)
        dec2 = self.brain.evaluate(ctx2)
        self.assertEqual(dec2.surf_state, SurfState.MULTI_MODEL)

    def test_logging(self):
        """Test that decisions are logged"""
        ctx = SurfingContext("2025-01-01 10:00:00", Regime.EAT, 0.5, 0.1, 0.0)
        try:
            self.brain.evaluate(ctx)
        except Exception as e:
            print(f"Logging failed with error: {e}")
            raise e
        
        today = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"decisions_{today}.csv"
        
        self.assertTrue(log_file.exists())
        with open(log_file, 'r') as f:
            lines = f.readlines()
            self.assertTrue(len(lines) >= 2) # Header + 1 row

if __name__ == '__main__':
    unittest.main()
