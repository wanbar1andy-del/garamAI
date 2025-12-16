import unittest
import pandas as pd
import shutil
from pathlib import Path
import sys
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.loaders.kr_minute_loader import KRMinuteLoader
from config import PATHS

# Setup logging
logging.basicConfig(level=logging.INFO)

class TestKRMinuteLoader(unittest.TestCase):
    
    def setUp(self):
        """Create dummy data for testing"""
        self.loader = KRMinuteLoader()
        self.test_symbol = "TEST01"
        self.interval = "1"
        
        # Define test path
        self.test_dir = PATHS.KR_ROOT / "intraday" / f"{self.interval}m"
        self.test_file = self.test_dir / f"{self.test_symbol}_{self.interval}m.csv"
        
        # Create directory
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dummy CSV
        data = {
            'timestamp': [
                '2023-10-25 09:00:00',
                '2023-10-25 09:01:00',
                '2023-10-25 09:02:00'
            ],
            'open': [1000, 1010, 1020],
            'high': [1020, 1030, 1040],
            'low': [990, 1000, 1010],
            'close': [1010, 1020, 1030],
            'volume': [100, 200, 300]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_file, index=False)
        
    def tearDown(self):
        """Clean up test data"""
        if self.test_file.exists():
            self.test_file.unlink()
            
    def test_load_success(self):
        """Test successful loading"""
        df = self.loader.load(self.test_symbol, self.interval)
        
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertIsInstance(df.index, pd.DatetimeIndex)
        self.assertEqual(df.index[0], pd.Timestamp('2023-10-25 09:00:00'))
        self.assertEqual(df['close'].iloc[-1], 1030)
        
    def test_load_not_found(self):
        """Test loading non-existent symbol"""
        df = self.loader.load("INVALID", self.interval)
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()
