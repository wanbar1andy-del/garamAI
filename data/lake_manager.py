import os
import pandas as pd
from typing import Optional, Dict, Any
import logging
from .loaders.local_loader import LocalLoader
from .loaders.drive_loader import DriveLoader

logger = logging.getLogger(__name__)

class LakeManager:
    """
    Central access point for the Data Lake.
    Routes requests to Local Cache or Google Drive based on availability and policy.
    """
    
    def __init__(self, local_path: str = "data_lake/local_cache", drive_path: str = "data_lake/raw"):
        self.local_path = local_path
        self.drive_path = drive_path
        self.local_loader = LocalLoader(local_path)
        self.drive_loader = DriveLoader(drive_path)
        logger.info(f"LakeManager initialized. Local: {local_path}, Drive: {drive_path}")

    def get_price_history(self, symbol: str, timeframe: str, start_date: str = None, end_date: str = None, market: str = 'us') -> pd.DataFrame:
        """
        Retrieve price history (OHLCV) for a given symbol and timeframe.
        Logic: Check local -> if missing, fetch from Drive -> cache to local -> return
        """
        logger.info(f"Requesting data for {symbol} ({timeframe})")
        
        # 1. Try Local
        df = self.local_loader.load(symbol, timeframe, market)
        
        if df is not None and not df.empty:
            # TODO: Check if date range covers request. For now, assume if exists, it's good or we append.
            # In v0, we just return what we have if it exists.
            logger.info("Data found in Local Cache.")
            return self._filter_date_range(df, start_date, end_date)
            
        # 2. Try Drive
        logger.info("Data not found in Local. Searching Drive...")
        df = self.drive_loader.load(symbol, timeframe, market)
        
        if df is not None and not df.empty:
            logger.info("Data found in Drive. Caching to Local...")
            self.local_loader.save(df, symbol, timeframe, market)
            return self._filter_date_range(df, start_date, end_date)
            
        logger.warning(f"Data not found for {symbol} in Lake.")
        return pd.DataFrame()

    def _filter_date_range(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        if df.empty:
            return df
            
        # Ensure datetime index or column
        if 'timestamp' in df.columns:
            col = 'timestamp'
        elif 'date' in df.columns:
            col = 'date'
        else:
            return df
            
        mask = pd.Series(True, index=df.index)
        if start_date:
            mask &= (df[col] >= pd.to_datetime(start_date))
        if end_date:
            mask &= (df[col] <= pd.to_datetime(end_date))
            
        return df[mask]

    def save_data(self, data: pd.DataFrame, symbol: str, timeframe: str, mode: str = 'local', market: str = 'us'):
        """
        Save data to the lake.
        """
        if mode in ['local', 'both']:
            self.local_loader.save(data, symbol, timeframe, market)
        
        # Drive save is usually manual or batch, but we can support it
        # DriveLoader doesn't have save yet (read-only for now as per plan), but we can add if needed.
        # For now, LakeManager only writes to Local.
        if mode == 'drive':
            logger.warning("Direct write to Drive not yet implemented in LakeManager.")
