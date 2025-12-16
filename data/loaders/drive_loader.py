import pandas as pd
import os
import glob
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class DriveLoader:
    """
    Handles data loading from Google Drive (Data Lake).
    Optimized for archival and batch retrieval.
    Structure: {base_path}/{market}/{symbol}/{timeframe}/...
    """
    
    def __init__(self, base_path: str):
        self.base_path = base_path

    def _get_search_path(self, symbol: str, timeframe: str, market: str = 'us') -> str:
        # Example: data_lake/raw/us/sp500/1d/
        # We might need a mapping or just assume structure
        # For now, let's try to find the symbol directory
        # Assuming: {base_path}/{market}/{symbol_group}/{timeframe}
        # But user structure was: raw/us/sp500/1d
        
        # Let's simplify: base_path points to 'raw'
        # We look for {market}/*/{timeframe} containing the symbol?
        # Or just assume {market}/{symbol}/{timeframe} for now as per LocalLoader
        
        # User's example: us/sp500/1d
        # Maybe 'sp500' is the symbol? Or a group?
        # Let's assume symbol is the directory name for simplicity in v0.
        
        safe_symbol = symbol.replace(':', '_')
        return os.path.join(self.base_path, market, safe_symbol, timeframe)

    def load(self, symbol: str, timeframe: str, market: str = 'us') -> Optional[pd.DataFrame]:
        """Load data from Drive. Handles partitioned files."""
        search_dir = self._get_search_path(symbol, timeframe, market)
        
        if not os.path.exists(search_dir):
            # Try checking if it's a file directly (e.g. symbol.parquet)
            file_path = f"{search_dir}.parquet"
            if os.path.exists(file_path):
                try:
                    return pd.read_parquet(file_path)
                except Exception as e:
                    logger.error(f"Failed to read drive file {file_path}: {e}")
                    return None
            return None
            
        # If directory, look for parquet files (partitioned by year/month)
        files = glob.glob(os.path.join(search_dir, "**/*.parquet"), recursive=True)
        if not files:
            return None
            
        try:
            logger.info(f"Found {len(files)} files in Drive for {symbol}")
            dfs = [pd.read_parquet(f) for f in files]
            full_df = pd.concat(dfs, ignore_index=True)
            
            # Sort and deduplicate
            if 'timestamp' in full_df.columns:
                full_df['timestamp'] = pd.to_datetime(full_df['timestamp'])
                full_df.sort_values('timestamp', inplace=True)
                full_df.drop_duplicates(subset=['timestamp'], keep='last', inplace=True)
            elif 'date' in full_df.columns:
                full_df['date'] = pd.to_datetime(full_df['date'])
                full_df.sort_values('date', inplace=True)
                full_df.drop_duplicates(subset=['date'], keep='last', inplace=True)
                
            return full_df
        except Exception as e:
            logger.error(f"Failed to load partitioned data from {search_dir}: {e}")
            return None

    def list_available_data(self) -> List[str]:
        """List all available datasets in Drive."""
        # Just walk the directory and find leaf directories with parquet files
        datasets = []
        for root, dirs, files in os.walk(self.base_path):
            if any(f.endswith('.parquet') for f in files):
                datasets.append(root)
        return datasets
