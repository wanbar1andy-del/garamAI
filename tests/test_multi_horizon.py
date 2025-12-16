import unittest
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.research.regime.miracle_engine import CoordinationEngine, Policy, MiracleBacktester, ImmediateBreakoutEntry, StandardRisk

class TestCoordinationEngine(unittest.TestCase):
    def setUp(self):
        self.rules = [
            {
                "state": "FLAT",
                "rules": [
                    {
                        "condition": "fs > 0.5 and fm >= 0",
                        "action": "ENTER_LONG",
                        "params": {"size_mod": 1.0}
                    },
                    {
                        "condition": "fs < -0.5 and fm <= 0",
                        "action": "ENTER_SHORT",
                        "params": {"size_mod": 1.0}
                    }
                ]
            },
            {
                "state": "LONG",
                "rules": [
                    {
                        "condition": "fs < 0 and fm < 0",
                        "action": "EXIT_ALL",
                        "params": {"reason": "TrendReversal"}
                    }
                ]
            }
        ]
        self.engine = CoordinationEngine(self.rules)

    def test_flat_entry_long(self):
        action, params = self.engine.evaluate("FLAT", 0.6, 0.1)
        self.assertEqual(action, "ENTER_LONG")
        self.assertEqual(params['size_mod'], 1.0)

    def test_flat_entry_short(self):
        action, params = self.engine.evaluate("FLAT", -0.6, -0.1)
        self.assertEqual(action, "ENTER_SHORT")

    def test_flat_no_entry(self):
        action, params = self.engine.evaluate("FLAT", 0.1, 0.1)
        self.assertEqual(action, "WAIT")

    def test_long_exit(self):
        action, params = self.engine.evaluate("LONG", -0.1, -0.1)
        self.assertEqual(action, "EXIT_ALL")
        self.assertEqual(params['reason'], "TrendReversal")

    def test_long_hold(self):
        action, params = self.engine.evaluate("LONG", 0.1, 0.1)
        self.assertEqual(action, "WAIT")

    def test_priority(self):
        # Add conflicting rules with different priorities
        self.rules[0]['rules'].append({
            "condition": "fs > 0.5",
            "action": "LOW_PRIORITY_ACTION",
            "priority": 10
        })
        self.rules[0]['rules'].append({
            "condition": "fs > 0.5",
            "action": "HIGH_PRIORITY_ACTION",
            "priority": 100
        })
        # Re-init engine
        self.engine = CoordinationEngine(self.rules)
        
        action, params = self.engine.evaluate("FLAT", 0.6, 0.1)
        self.assertEqual(action, "HIGH_PRIORITY_ACTION")

if __name__ == '__main__':
    unittest.main()
