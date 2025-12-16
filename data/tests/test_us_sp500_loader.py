"""
Tests for US S&P500 Data Loader
"""

import unittest
import pandas as pd
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.loaders.us_sp500_loader import USSP500DataLoader
from config import PATHS

class TestUSSP500DataLoader(unittest.TestCase):
    
    def setUp(self):
        self.loader = USSP500DataLoader()
        # Create mock data directory
        self.mock_dir = PATHS.US_SP500_ROOT / "prices_daily"
        self.mock_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock price files
        self.create_mock_price_file("AAPL")
        self.create_mock_price_file("MSFT")
        
    def create_mock_price_file(self, symbol):
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        data = {
            'date': dates,
            'open': [100.0] * len(dates),
            'high': [105.0] * len(dates),
            'low': [95.0] * len(dates),
            'close': [102.0] * len(dates),
            'volume': [1000000] * len(dates)
        }
        df = pd.DataFrame(data)
        df.to_csv(self.mock_dir / f"{symbol}.csv", index=False)

    def tearDown(self):
        # Clean up mock files
        if self.mock_dir.exists():
            for f in self.mock_dir.glob("*.csv"):
                f.unlink()

    def test_get_prices(self):
        """Test loading prices for specific symbols"""
        symbols = ["AAPL", "MSFT"]
        start_date = "2023-01-01"
        end_date = "2023-01-10"
        
        df = self.loader.get_prices(symbols, start_date, end_date)
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df['symbol'].unique()), 2)
        self.assertTrue('AAPL' in df['symbol'].values)
        self.assertTrue('MSFT' in df['symbol'].values)
        
    def test_get_universe_and_prices(self):
        """Test universe filtering by history length"""
        # AAPL has 365 days (enough)
        # Create a short history symbol
        dates = pd.date_range(start="2023-12-01", end="2023-12-31", freq="D")
        short_data = {
            'date': dates,
            'open': [10.0] * len(dates),
            'high': [11.0] * len(dates),
            'low': [9.0] * len(dates),
            'close': [10.5] * len(dates),
            'volume': [100] * len(dates)
        }
        pd.DataFrame(short_data).to_csv(self.mock_dir / "SHORT.csv", index=False)
        
        symbols, prices = self.loader.get_universe_and_prices(
            start_date="2023-01-01", 
            end_date="2023-12-31", 
            min_history_days=100
        )
        
        self.assertIn("AAPL", symbols)
        self.assertIn("MSFT", symbols)
        self.assertNotIn("SHORT", symbols)
        
        # Cleanup
        (self.mock_dir / "SHORT.csv").unlink()

if __name__ == '__main__':
    unittest.main()
