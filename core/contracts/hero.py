from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class HeroMetadata:
    """
    Hero Discovery Result Contract.
    """
    symbol: str
    is_hero: bool
    hero_score: float
    expectancy_net: float
    win_rate: float
    trades: int
    overnight_tier: str  # STRICT, SOFT, NONE
    
    # Additional debugging info
    meta: Optional[Dict[str, float]] = None
