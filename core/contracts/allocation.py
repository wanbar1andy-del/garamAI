from dataclasses import dataclass
from typing import Optional

@dataclass
class AllocationRow:
    """
    Capital Allocation Result.
    """
    symbol: str
    sleeve: str  # ALPHA, BETA, RESERVE
    tier: str    # ON-STRICT, ON-SOFT, NONE
    weight: float # 0.0 ~ 1.0 (Target Weight)
    notional: float # Target Value (KRW)
    reason: str
