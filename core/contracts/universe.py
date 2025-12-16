from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class UniverseRow:
    """
    Standard Universe Definition Contract.
    """
    symbol: str  # 6-digit code
    meta: Optional[Dict[str, Any]] = None  # Flexible metadata (sector, market_cap, etc.)

    def __post_init__(self):
        if len(self.symbol) != 6:
            raise ValueError(f"Symbol must be 6 digits: {self.symbol}")
