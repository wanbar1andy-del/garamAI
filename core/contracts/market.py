from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MarketSchema:
    """
    Standard Market Data Row (OHLCV).
    """
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # Optional fields for extended data (e.g. trading value)
    value: Optional[float] = None
