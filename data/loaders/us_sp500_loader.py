"""
US S&P500 Data Loader
Loader for survivorship-bias-minimized 20Y S&P500 daily data.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

class USSP500DataLoader:
    """
    Loader for survivorship-bias-minimized 20Y S&P500 daily data.

    Responsibilities:
    - Load historical index membership (constituents)
    - Load daily OHLCV for requested symbols/date ranges
    - Filter universe by 'in_index' status for a given date or date range
    """
    
    def __init__(self):
        self.local_root = PATHS.US_SP500_ROOT
        self.constituents_path = self.local_root / "constituents"
        self.prices_path = self.local_root / "prices_daily"
        self.meta_path = self.local_root / "meta"
        
        # Ensure directories exist
        self.constituents_path.mkdir(parents=True, exist_ok=True)
        self.prices_path.mkdir(parents=True, exist_ok=True)
        self.meta_path.mkdir(parents=True, exist_ok=True)

    def get_constituents(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Returns a DataFrame with columns: date, symbol, in_index
        Filtered between start_date and end_date.
        """
        # TODO: Implement actual loading from parquet/csv
        # For now, return empty DataFrame or mock if file doesn't exist
        # In real implementation, this would load from self.constituents_path
        
        # Mock implementation for initial testing if no data exists
        return pd.DataFrame(columns=['date', 'symbol', 'in_index'])

    def get_prices(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        Returns DataFrame with OHLCV for given symbols and date range.
        """
        all_prices = []
        
        for symbol in symbols:
            file_path = self.prices_path / f"{symbol}.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                df['date'] = pd.to_datetime(df['date'])
                
                # Filter by date
                mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
                filtered_df = df.loc[mask].copy()
                filtered_df['symbol'] = symbol
                all_prices.append(filtered_df)
        
        if not all_prices:
            return pd.DataFrame()
            
        return pd.concat(all_prices, ignore_index=True)

    def get_index_universe(self, date: str) -> List[str]:
        """
        For a given date, return the list of symbols that are in S&P500.
        """
        # Placeholder: In real impl, query get_constituents
        return []

    def get_universe_and_prices(self, start_date: str, end_date: str, min_history_days: int = 252) -> Tuple[List[str], pd.DataFrame]:
        """
        Returns:
        - symbols that have at least min_history_days of price history in the range
        - prices DataFrame for that universe
        """
        # 1. Get all potential symbols (from constituents or file list)
        # For now, scan directory
        available_files = list(self.prices_path.glob("*.csv"))
        all_symbols = [f.stem for f in available_files]
        
        if not all_symbols:
            return [], pd.DataFrame()
            
        # 2. Load prices
        prices_df = self.get_prices(all_symbols, start_date, end_date)
        
        if prices_df.empty:
            return [], pd.DataFrame()
            
        # 3. Filter by history length
        valid_symbols = []
        final_prices = []
        
        for symbol, group in prices_df.groupby('symbol'):
            if len(group) >= min_history_days:
                valid_symbols.append(symbol)
                final_prices.append(group)
                
        if not final_prices:
            return [], pd.DataFrame()
            
        return valid_symbols, pd.concat(final_prices, ignore_index=True)
