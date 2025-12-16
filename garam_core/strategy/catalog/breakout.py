# garam_core/strategy/catalog/breakout.py
import pandas as pd
from garam_core.strategy.base import BaseStrategy
from garam_core.engine.signals_short_term import signal_breakout

class BreakoutStrategy(BaseStrategy):
    NAME = "Breakout"
    
    def __init__(self, window: int = 10, vol_thr: float = 0.015):
        super().__init__(window=window, vol_thr=vol_thr)
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return signal_breakout(df, window=self.params["window"], vol_thr=self.params["vol_thr"])
