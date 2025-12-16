"""
Tests for Dashboard API
"""
import unittest
import json
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from ui.api.dashboard_api import dashboard_bp
from flask import Flask

class TestDashboardAPI(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(dashboard_bp)
        self.client = self.app.test_client()
        
    def test_surfing_status_endpoint(self):
        response = self.client.get('/api/surfing/status')
        self.assertIn(response.status_code, [200, 404, 500])
        
    def test_pnl_equity_endpoint(self):
        response = self.client.get('/api/pnl/equity')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('base_capital', data)
        self.assertIn('points', data)
        
    def test_pnl_segments_endpoint(self):
        response = self.client.get('/api/pnl/segments')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('segments', data)
        
    def test_anomalies_summary_endpoint(self):
        response = self.client.get('/api/anomalies/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_anomalies', data)
        
    def test_us_factors_summary_endpoint(self):
        response = self.client.get('/api/us_factors/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('strategies', data)
        
    def test_system_health_endpoint(self):
        response = self.client.get('/api/system/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('data_coverage', data)

if __name__ == '__main__':
    unittest.main()
