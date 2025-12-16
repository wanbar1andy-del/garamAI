"""
External API Provider
Abstract base class for external fundamental and price data providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd
from datetime import datetime

class ExternalAPIProvider(ABC):
    """
    Abstract base class for external data providers.
    
    Implementations should provide fundamental data and price history
    from external APIs (e.g., Sharadar, Polygon, Alpha Vantage).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize provider.
        
        Args:
            api_key: API key for authentication (optional)
        """
        self.api_key = api_key
        self.is_available = self._check_availability()
        
    @abstractmethod
    def _check_availability(self) -> bool:
        """
        Check if the API is available and accessible.
        
        Returns:
            True if API is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Get fundamental data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dict with fundamental metrics:
            {
                'symbol': str,
                'market_cap': float,
                'pe_ratio': float,
                'pb_ratio': float,
                'roe': float,
                'debt_to_equity': float,
                'revenue_growth': float,
                'profit_margin': float,
                'timestamp': datetime
            }
            Returns None if data unavailable
        """
        pass
    
    @abstractmethod
    def get_price_history(self, 
                         symbol: str, 
                         start_date: str, 
                         end_date: str) -> Optional[pd.DataFrame]:
        """
        Get historical price data for a symbol.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume
            Returns None if data unavailable
        """
        pass
    
    def get_multiple_fundamentals(self, symbols: list) -> Dict[str, Dict]:
        """
        Get fundamentals for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict mapping symbol to fundamental data
        """
        results = {}
        for symbol in symbols:
            data = self.get_fundamentals(symbol)
            if data:
                results[symbol] = data
        return results
