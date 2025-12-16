"""
Exit Engine Module
Manages trade exits (Stop Loss, Take Profit, Trailing Stop) based on Market Regime.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import sys
from pathlib import Path

# Add project root to path to import regime
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.regime.market_regime import MarketState

class ExitType(Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    TIME_STOP = "TIME_STOP"
    NONE = "NONE"

@dataclass
class ExitParams:
    stop_price: float
    target_price: float
    trailing_stop_price: Optional[float] = None
    entry_price: float = 0.0
    quantity: int = 0

class ExitEngine:
    """
    Calculates and manages exit levels based on volatility (ATR) and Market Regime.
    """
    
    def __init__(self):
        # Default Multipliers (Green Regime)
        self.default_stop_atr = 2.0
        self.default_target_r = 3.0
        
        # Regime Adjustments (Stop ATR multiplier)
        self.regime_stop_multipliers = {
            MarketState.GREEN: 2.0,   # Wide stop
            MarketState.YELLOW: 1.5,  # Tight stop
            MarketState.RED: 1.0      # Very tight stop (if holding)
        }
        
        # Regime Adjustments (Target R-multiple)
        self.regime_target_multipliers = {
            MarketState.GREEN: 3.0,   # Let winners run
            MarketState.YELLOW: 2.0,  # Take quick profits
            MarketState.RED: 1.5      # Defensive
        }

    def calculate_initial_levels(self, entry_price: float, atr: float, regime: MarketState, direction: str = 'long') -> ExitParams:
        """
        Calculate initial Stop Loss and Take Profit levels.
        """
        stop_mult = self.regime_stop_multipliers.get(regime, self.default_stop_atr)
        target_mult = self.regime_target_multipliers.get(regime, self.default_target_r)
        
        stop_dist = atr * stop_mult
        risk = stop_dist
        reward = risk * target_mult # Target based on R-multiple of the stop distance
        
        if direction == 'long':
            stop_price = entry_price - stop_dist
            target_price = entry_price + reward
        else: # short
            stop_price = entry_price + stop_dist
            target_price = entry_price - reward
            
        return ExitParams(
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            trailing_stop_price=stop_price # Initial trailing stop is same as initial stop
        )

    def update_trailing_stop(self, current_price: float, current_stop: float, atr: float, regime: MarketState, direction: str = 'long') -> float:
        """
        Update trailing stop price. Ratchet up only (for long).
        Uses ATR-based trailing distance.
        """
        stop_mult = self.regime_stop_multipliers.get(regime, self.default_stop_atr)
        trail_dist = atr * stop_mult
        
        if direction == 'long':
            potential_new_stop = current_price - trail_dist
            # Only move up
            return max(current_stop, potential_new_stop)
        else: # short
            potential_new_stop = current_price + trail_dist
            # Only move down
            return min(current_stop, potential_new_stop)

    def check_exit(self, current_price: float, params: ExitParams, direction: str = 'long') -> ExitType:
        """
        Check if price has hit Stop Loss or Take Profit.
        """
        if direction == 'long':
            if current_price <= params.stop_price:
                return ExitType.STOP_LOSS
            if params.trailing_stop_price and current_price <= params.trailing_stop_price:
                 return ExitType.TRAILING_STOP
            if current_price >= params.target_price:
                return ExitType.TAKE_PROFIT
        else: # short
            if current_price >= params.stop_price:
                return ExitType.STOP_LOSS
            if params.trailing_stop_price and current_price >= params.trailing_stop_price:
                return ExitType.TRAILING_STOP
            if current_price <= params.target_price:
                return ExitType.TAKE_PROFIT
                
        return ExitType.NONE
