from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SignalRecord:
    """
    Standard Trading Signal.
    """
    symbol: str
    timestamp: datetime
    action: str  # BUY, SELL, HOLD, EXIT
    strength: float  # 0.0 ~ 1.0 or -1.0 ~ 1.0
    reason: str
    meta: Optional[dict] = None
