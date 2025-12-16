"""
Test UI API Endpoints (Phase 3)
Verifies:
1. Kiwoom Login Trigger
2. AI Chat Response
3. Detailed Portfolio Data
"""

import unittest
import sys
import json
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.server import app

class TestUIEndpoints(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_login_trigger(self):
        """Test POST /api/system/login_kiwoom"""
        response = self.app.post('/api/system/login_kiwoom')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'triggered')
        print("\n✅ Login Trigger: PASS")

    def test_ai_chat(self):
        """Test POST /api/ai/chat"""
        # 1. Portfolio Query
        response = self.app.post('/api/ai/chat', json={'message': 'Show me my portfolio'})
        data = json.loads(response.data)
        self.assertIn('Samsung Elec', data['response'])
        print("\n✅ AI Chat (Portfolio): PASS")
        
        # 2. Why Query
        response = self.app.post('/api/ai/chat', json={'message': 'Why did you buy?'})
        data = json.loads(response.data)
        self.assertIn('Foreigner Net Buy', data['response'])
        print("\n✅ AI Chat (Reasoning): PASS")

    def test_portfolio_detailed(self):
        """Test GET /api/portfolio/detailed"""
        response = self.app.get('/api/portfolio/detailed')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('positions', data)
        self.assertEqual(len(data['positions']), 4)
        
        # Check structure
        first_pos = data['positions'][0]
        self.assertIn('color', first_pos)
        self.assertIn('reason', first_pos)
        self.assertIn('params', first_pos)
        print("\n✅ Portfolio Detailed Data: PASS")

if __name__ == "__main__":
    unittest.main()
