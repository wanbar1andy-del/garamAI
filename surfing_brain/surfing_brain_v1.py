"""
Surfing Brain v1
Simple regime-based decision engine (stub for Phase 4).
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class MarketState:
    """Current market state"""
    regime: str  # "EAT", "HURT", "DEATH"
    uncertainty: float  # 0.0 - 1.0
    recent_expectancy_r: float
    recent_drawdown: float

@dataclass
class Decision:
    """Surfing Brain decision"""
    mode: str  # "AGGRESSIVE", "CONSERVATIVE", "DEFENSIVE"
    risk_multiplier: float  # 0.0 - 1.0
    kr_allocation: float
    us_allocation: float

class SurfingBrain:
    """
    Surfing Brain v1 - Simple decision engine.
    
    Makes allocation decisions based on regime and market conditions.
    """
    
    def __init__(self, config: Dict = None):
        """Initialize Surfing Brain"""
        self.config = config or {}
        
    def decide(self, state: MarketState) -> Decision:
        """
        Make allocation decision based on market state.
        
        Args:
            state: Current market state
            
        Returns:
            Decision with mode, risk multiplier, and allocations
        """
        # Simple rule-based logic
        if state.regime == "EAT" and state.uncertainty < 0.4:
            mode = "AGGRESSIVE"
            risk_mult = 0.8
        elif state.regime == "HURT" or state.uncertainty > 0.6:
            mode = "CONSERVATIVE"
            risk_mult = 0.4
        else:
            mode = "DEFENSIVE"
            risk_mult = 0.2
        
        # Adjust for drawdown
        if state.recent_drawdown > 0.1:
            risk_mult *= 0.5
        
        # Simple allocation
        kr_alloc = 0.4 * risk_mult
        us_alloc = 0.5 * risk_mult
        
        return Decision(
            mode=mode,
            risk_multiplier=risk_mult,
            kr_allocation=kr_alloc,
            us_allocation=us_alloc
        )
