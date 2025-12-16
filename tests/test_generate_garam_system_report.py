"""
Test System Report Generation
"""
import unittest
from pathlib import Path
import sys
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.generate_garam_system_report import generate_report
from config import PATHS

class TestGenerateReport(unittest.TestCase):
    def test_generate_report(self):
        # Ensure output dir exists
        (PATHS.DATA_DIR / "reports").mkdir(parents=True, exist_ok=True)
        
        # Run generation
        generate_report()
        
        # Check if any report was created
        reports = list((PATHS.DATA_DIR / "reports").glob("garam_system_report_*.md"))
        self.assertTrue(len(reports) > 0)
        
        # Check content of latest report
        latest_report = sorted(reports)[-1]
        with open(latest_report, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Garam System Health Report", content)
            self.assertIn("Overview", content)

if __name__ == '__main__':
    unittest.main()
