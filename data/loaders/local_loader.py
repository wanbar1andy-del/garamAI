import pandas as pd
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class LocalLoader:
    """
    Handles data loading from local SSD/HDD cache.
    Optimized for speed using Parquet.
    Structure: {base_path}/{market}/{symbol}/{timeframe}.parquet
    """
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)

    def _get_file_path(self, symbol: str, timeframe: str, market: str = 'us') -> str:
        # Sanitize symbol for filename
        safe_symbol = symbol.replace(':', '_')
        return os.path.join(self.base_path, market, safe_symbol, f"{timeframe}.parquet")

    def load(self, symbol: str, timeframe: str, market: str = 'us') -> Optional[pd.DataFrame]:
        """Load data from local storage."""
        file_path = self._get_file_path(symbol, timeframe, market)
        
        if os.path.exists(file_path):
            try:
                df = pd.read_parquet(file_path)
                logger.debug(f"Loaded {symbol} ({timeframe}) from local cache.")
                return df
            except Exception as e:
                logger.error(f"Failed to read local parquet {file_path}: {e}")
                return None
        return None

    def save(self, df: pd.DataFrame, symbol: str, timeframe: str, market: str = 'us'):
        """Save data to local storage."""
        file_path = self._get_file_path(symbol, timeframe, market)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            df.to_parquet(file_path)
            logger.debug(f"Saved {symbol} ({timeframe}) to local cache: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save local parquet {file_path}: {e}")
