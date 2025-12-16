# garam_core/strategy/base.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    Abstract Base Class for all GARAM strategies.
    Simplified: name defined as class attribute.
    """
    NAME = "Base"
    
    def __init__(self, **kwargs):
        # Allow params override if needed, but keep simple
        self.params = kwargs

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Returns a Series of signals: 1 (Long), -1 (Short), 0 (Neutral).
        """
        pass
    
    def __repr__(self):
        return f"<{self.NAME}>"
