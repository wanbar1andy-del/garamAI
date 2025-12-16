"""
Fetch Historical Data for Regime Lab
Fetches 20 years of daily OHLCV data for KOSPI and S&P 500 using yfinance.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS

def fetch_data():
    # Targets: KOSPI (^KS11), S&P 500 (^GSPC)
    symbols = {
        'KR': '^KS11',
        'US': '^GSPC'
    }
    
    start_date = "2005-01-01"
    end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    history_dir = PATHS.DATA_DIR / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    
    for market, symbol in symbols.items():
        print(f"Fetching {market} ({symbol}) from {start_date} to {end_date}...")
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                print(f"Warning: No data found for {symbol}")
                continue
                
            # Standardize columns
            # yfinance returns MultiIndex columns sometimes, flatten them
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            df = df.rename(columns={'date': 'timestamp', 'adj close': 'close'}) # Use Adj Close as Close for long term
            
            # Save
            output_file = history_dir / f"{market}_daily_20y.csv"
            df.to_csv(output_file, index=False)
            print(f"Saved to {output_file} ({len(df)} rows)")
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

if __name__ == "__main__":
    fetch_data()
