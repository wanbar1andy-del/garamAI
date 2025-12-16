"""
Test Data Validation Script
"""
import unittest
from pathlib import Path
import sys
import shutil
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.validate_us_sp500_data_coverage import validate_coverage
from config import PATHS

class TestValidateCoverage(unittest.TestCase):
    def setUp(self):
        # Create mock data
        self.mock_dir = PATHS.US_SP500_ROOT / "prices_daily"
        self.mock_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy price file
        df = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=10),
            'close': [100] * 10
        })
        df.to_csv(self.mock_dir / "TEST_SYM.csv", index=False)
        
    def test_validate_coverage(self):
        report = validate_coverage()
        self.assertGreater(report['total_symbols'], 0)
        self.assertIn('TEST_SYM', [f.stem for f in self.mock_dir.glob("*.csv")])
        
    def tearDown(self):
        # Cleanup mock file
        (self.mock_dir / "TEST_SYM.csv").unlink(missing_ok=True)

if __name__ == '__main__':
    unittest.main()
