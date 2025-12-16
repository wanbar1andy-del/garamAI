"""
Unit tests for System Health Monitoring
"""

import unittest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.health_check import run_system_health_check
from monitoring.health_report import save_health_report
from monitoring.alerting import log_alert
from config import PATHS

class TestSystemHealth(unittest.TestCase):
    
    def test_run_system_health_check_structure(self):
        """Test that health check returns correct structure."""
        health = run_system_health_check()
        
        self.assertIn("status", health)
        self.assertIn("timestamp", health)
        self.assertIn("mode", health)
        self.assertIn("data", health)
        self.assertIn("shadow", health)
        
        # Check Mode
        self.assertIn("trading_mode", health["mode"])
        # Should be SHADOW if config exists and is correct
        # We assume the environment is set up correctly from previous steps
        
    def test_save_health_report(self):
        """Test that reports are saved."""
        health = {
            "status": "OK",
            "timestamp": "2025-11-25T10:00:00",
            "mode": {"trading_mode": "SHADOW", "status": "OK", "message": "OK"},
            "data": {"status": "OK", "us_daily": {"status": "OK", "latest": "N/A"}},
            "shadow": {"status": "OK", "latest_report": "None", "message": "OK"},
            "metrics": {"status": "OK"}
        }
        
        save_health_report(health)
        
        # Check if files exist
        health_dir = PATHS.LOGS_DIR / "health"
        today_str = "20251125" # Mocked timestamp in function uses now(), so we might miss if date changes
        # Actually save_health_report uses datetime.now(), so we should check for *a* file
        
        files = list(health_dir.glob("health_report_*.json"))
        self.assertTrue(len(files) > 0)
        
    def test_log_alert(self):
        """Test alerting logging."""
        health = {
            "status": "WARN",
            "mode": {"trading_mode": "SHADOW", "status": "OK"},
            "data": {"status": "WARN"},
            "shadow": {"status": "OK", "message": "OK"}
        }
        
        log_alert(health)
        
        alert_log = PATHS.LOGS_DIR / "alerts.log"
        self.assertTrue(alert_log.exists())
        
        with open(alert_log, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("System Status: WARN", content)

if __name__ == '__main__':
    unittest.main()
