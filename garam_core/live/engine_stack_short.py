# garam_core/live/engine_stack_short.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pandas as pd

# Import base classes
from garam_core.live.engine_stack import EngineStack, EngineStackSpec, StackDecision

@dataclass
class StackDecisionShort(StackDecision):
    side: str = "HOLD" # LONG, SHORT, HOLD

class EngineStackShort(EngineStack):
    """
    Extended EngineStack for Long/Short strategies.
    Overrides on_bar to return StackDecisionShort using derived logic.
    """
    def __init__(self, spec: EngineStackSpec):
        super().__init__(spec)
        # self.state inherited

    def on_bar(
        self, 
        ts: pd.Timestamp, 
        df: pd.DataFrame, 
        fear_score: float, 
        fear_series: Optional[pd.Series] = None
    ) -> StackDecisionShort:
        """
        Long/Short 진입 대응
        """
        # 1. Base Logic (Regime -> Signal -> Turbo -> etc.)
        base_dec = super().on_bar(ts, df, fear_score, fear_series)

        # 2. Map Action to Side
        # "Profit-First" logic usually means Long-Only unless specifically adapted.
        # But here we assume the Base Signal might produce "BUY" or "SELL" based on new logic?
        # Or, we strictly map:
        #   BUY -> LONG Entry
        #   SELL -> SHORT Entry?
        # NO, standard engine "SELL" usually means "Exit Long".
        # If we want Short Entry, we need a signal that says "SHORT".
        # However, the user provided snippet says:
        #   if action == "BUY": side = "LONG"
        #   elif action == "SELL": side = "SHORT"
        # This implies standard SELL signal acts as SHORT Entry? 
        # Or implies we are flipping bias?
        # Let's stick to the User Snippet logic exactly.
        
        action = base_dec.action
        side = "HOLD"

        if action == "BUY":
            side = "LONG"
        elif action == "SELL":
            # NOTE: In standard engine, SELL is Exit. 
            # Here, it is treated as SHORT side entry/bias.
            side = "SHORT"
        
        return StackDecisionShort(
            ts=base_dec.ts,
            action=base_dec.action,
            side=side,
            reason=base_dec.reason,
            multiplier=base_dec.multiplier,
            fear_score=base_dec.fear_score,
            regime=base_dec.regime,
            qty_frac=base_dec.qty_frac,
            debug=base_dec.debug,
        )
