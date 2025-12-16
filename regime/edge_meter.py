from dataclasses import dataclass
from typing import Tuple

@dataclass
class MarketState:
    """Snapshot of market indicators for regime classification"""
    trend_20d: float       # 20-day return
    atr_z: float           # Normalized ATR (0~1 percentile)
    fm: float              # Daily Trend Score
    fs_orb: float          # Intraday ORB Score
    fs_fast: float         # Intraday Momentum Score
    timestamp: str         # Current timestamp

class EdgeMeter:
    """
    EdgeMeter: The 'Volume Knob' of the DGE Engine.
    Responsibility:
    1. Classify Market Regime (R1~R7) based on MarketState.
    2. Calculate 'Edge Intensity' (0.0 ~ 1.0) for risk modulation.
    """
    
    def __init__(self):
        pass
        
    def classify_regime(self, state: MarketState) -> str:
        """
        Classify MarketState into R1~R7.
        Logic matches tag_regimes_for_hybrid.py.
        """
        # 1. Check Event/Risk-Off (R7) - Placeholder
        # if state.is_event_day: return "R7_EVENT_RISK_OFF"
        
        # 2. Up Trend
        if state.trend_20d > 0.03: # Strong Up
            if state.atr_z >= 0.7:
                return "R1_STRONG_UP_BREAKOUT"
            else:
                return "R2_STRONG_UP_GRIND"
                
        # 3. Down Trend
        elif state.trend_20d < -0.03: # Strong Down
            if state.atr_z >= 0.7:
                return "R6_STRONG_DOWN_CRASH"
            else:
                return "R5_WEAK_DOWN_DRIFT"
                
        # 4. Sideways
        else: # Flat (-0.03 ~ 0.03)
            if state.atr_z >= 0.6: # Choppy
                return "R4_SIDEWAYS_RANGE_HIGHVOL"
            else:
                return "R3_SIDEWAYS_RANGE_LOWVOL"
                
    def get_intensity(self, regime_id: str) -> float:
        """
        Get default intensity for a regime.
        This can be enhanced with dynamic logic (e.g. recent PnL).
        For now, returns static base intensity.
        """
        # Default Base Intensity Map (can be overridden by Playbook)
        base_intensity = {
            "R1_STRONG_UP_BREAKOUT": 0.8,
            "R2_STRONG_UP_GRIND": 0.5,
            "R3_SIDEWAYS_RANGE_LOWVOL": 0.6,
            "R4_SIDEWAYS_RANGE_HIGHVOL": 0.3, # Risky
            "R5_WEAK_DOWN_DRIFT": 0.7,
            "R6_STRONG_DOWN_CRASH": 1.0, # Attack!
            "R7_STRONG_DOWN_REVERSAL": 0.4
        }
        return base_intensity.get(regime_id, 0.5)
