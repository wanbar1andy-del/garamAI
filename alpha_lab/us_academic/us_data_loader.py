"""
US Data Loader
Fetches and caches US stock market data using Yahoo Finance
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Optional, List
import time

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed. Install with: pip install yfinance")


class USDataLoader:
    """
    US stock data loader with Yahoo Finance integration
    Handles data fetching, caching, and quality validation
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize US Data Loader
        
        Args:
            cache_dir: Directory for caching data (default: GARAM_Data/us_data)
        """
        if cache_dir is None:
            try:
                from garam.config import PATHS
                cache_dir = PATHS.DATA_DIR / "us_data"
            except ImportError:
                cache_dir = Path("GARAM_Data/us_data")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"USDataLoader initialized with cache: {self.cache_dir}")
    
    def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            use_cache: Use cached data if available
        
        Returns:
            DataFrame with OHLCV data
        """
        if not YFINANCE_AVAILABLE:
            logger.error("yfinance not available, using mock data")
            return self._generate_mock_data(symbol, start_date, end_date)
        
        # Check cache first
        if use_cache:
            cached_data = self._load_from_cache(symbol, start_date, end_date)
            if cached_data is not None:
                logger.info(f"Loaded {symbol} from cache ({len(cached_data)} rows)")
                return cached_data
        
        # Fetch from Yahoo Finance
        logger.info(f"Fetching {symbol} from Yahoo Finance...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Standardize column names
            df = self._standardize_columns(df)
            
            # Validate data quality
            df = self._validate_data(df, symbol)
            
            # Save to cache
            self._save_to_cache(df, symbol)
            
            logger.info(f"Fetched {symbol}: {len(df)} rows from {df.index[0]} to {df.index[-1]}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        use_cache: bool = True,
        delay: float = 0.5
    ) -> dict:
        """
        Fetch data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Use cached data if available
            delay: Delay between requests (seconds) to avoid rate limiting
        
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Fetching {i+1}/{len(symbols)}: {symbol}")
            
            df = self.fetch_data(symbol, start_date, end_date, use_cache)
            if not df.empty:
                results[symbol] = df
            
            # Rate limiting
            if i < len(symbols) - 1:
                time.sleep(delay)
        
        logger.info(f"Fetched {len(results)}/{len(symbols)} symbols successfully")
        return results
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to lowercase"""
        df.columns = df.columns.str.lower()
        
        # Rename if needed
        rename_map = {
            'adj close': 'adj_close'
        }
        df.rename(columns=rename_map, inplace=True)
        
        return df
    
    def _validate_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Validate data quality
        - Remove rows with missing OHLC data
        - Detect and handle outliers
        - Ensure chronological order
        """
        if df.empty:
            return df
        
        # Check for required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"{symbol}: Missing columns {missing_cols}")
            return df
        
        # Remove rows with missing OHLC
        before_count = len(df)
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        after_count = len(df)
        
        if before_count > after_count:
            logger.warning(f"{symbol}: Removed {before_count - after_count} rows with missing OHLC")
        
        # Detect price outliers (> 10x daily change)
        if len(df) > 1:
            pct_change = df['close'].pct_change().abs()
            outliers = pct_change > 10.0
            if outliers.any():
                logger.warning(f"{symbol}: Detected {outliers.sum()} potential outliers")
                # Don't remove automatically, just log
        
        # Ensure chronological order
        df = df.sort_index()
        
        return df
    
    def _load_from_cache(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str]
    ) -> Optional[pd.DataFrame]:
        """Load data from cache if available and covers date range"""
        cache_file = self.cache_dir / f"{symbol}.csv"
        
        if not cache_file.exists():
            return None
        
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            
            # Check if cache covers requested date range
            cache_start = df.index.min()
            cache_end = df.index.max()
            
            req_start = pd.to_datetime(start_date)
            req_end = pd.to_datetime(end_date) if end_date else pd.Timestamp.now()
            
            if cache_start <= req_start and cache_end >= req_end:
                # Filter to requested range
                mask = (df.index >= req_start) & (df.index <= req_end)
                return df[mask]
            else:
                logger.debug(f"{symbol}: Cache doesn't cover full range, will refetch")
                return None
                
        except Exception as e:
            logger.warning(f"Error loading cache for {symbol}: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame, symbol: str):
        """Save data to cache"""
        if df.empty:
            return
        
        cache_file = self.cache_dir / f"{symbol}.csv"
        
        try:
            df.to_csv(cache_file)
            logger.debug(f"Saved {symbol} to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Error saving cache for {symbol}: {e}")
    
    def _generate_mock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """Generate mock data for testing when yfinance is not available"""
        logger.warning(f"Generating mock data for {symbol}")
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date) if end_date else pd.Timestamp.now()
        
        dates = pd.date_range(start, end, freq='D')
        
        # Generate realistic price movement
        base_price = 100.0
        returns = np.random.randn(len(dates)) * 0.02  # 2% daily volatility
        prices = base_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(len(dates)) * 0.005),
            'high': prices * (1 + np.abs(np.random.randn(len(dates))) * 0.01),
            'low': prices * (1 - np.abs(np.random.randn(len(dates))) * 0.01),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates)),
            'adj_close': prices
        }, index=dates)
        
        return df
    
    def get_cache_info(self, symbol: str) -> dict:
        """Get information about cached data for a symbol"""
        cache_file = self.cache_dir / f"{symbol}.csv"
        
        if not cache_file.exists():
            return {'cached': False}
        
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            return {
                'cached': True,
                'rows': len(df),
                'start_date': str(df.index.min().date()),
                'end_date': str(df.index.max().date()),
                'file_size': cache_file.stat().st_size,
                'last_modified': datetime.fromtimestamp(cache_file.stat().st_mtime)
            }
        except Exception as e:
            return {'cached': True, 'error': str(e)}
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for a symbol or all symbols"""
        if symbol:
            cache_file = self.cache_dir / f"{symbol}.csv"
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for {symbol}")
        else:
            for cache_file in self.cache_dir.glob("*.csv"):
                cache_file.unlink()
            logger.info("Cleared all cache")


if __name__ == "__main__":
    # Test the loader
    logging.basicConfig(level=logging.INFO)
    
    loader = USDataLoader()
    
    # Test single symbol
    print("\n=== Testing single symbol fetch ===")
    df = loader.fetch_data("AAPL", "2023-01-01", "2023-12-31")
    if not df.empty:
        print(f"Fetched AAPL: {len(df)} rows")
        print(df.head())
        print(f"\nCache info: {loader.get_cache_info('AAPL')}")
    
    # Test multiple symbols
    print("\n=== Testing multiple symbols fetch ===")
    symbols = ["MSFT", "GOOGL", "AMZN"]
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-12-31")
    print(f"Fetched {len(results)} symbols")
    for symbol, df in results.items():
        print(f"{symbol}: {len(df)} rows")
