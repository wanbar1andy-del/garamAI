# garam_core/strategy/catalog/fear_contrarian.py
import pandas as pd
from garam_core.strategy.base import BaseStrategy
from garam_core.engine.signals_short_term import signal_fear_contrarian

class FearContrarianStrategy(BaseStrategy):
    NAME = "FearContrarian"
    
    def __init__(self, fear_hi: float = 0.85, fear_low: float = 0.15):
        super().__init__(fear_hi=fear_hi, fear_low=fear_low)
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fear = df.get("fear_score")
        if fear is None:
            fear = pd.Series(0.5, index=df.index)
        return signal_fear_contrarian(df, fear, fear_hi=self.params["fear_hi"], fear_low=self.params["fear_low"])
