from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseEngine(ABC):
    """
    Abstract Base Class for Trading Engines.
    All engines (Legacy, Advanced, etc.) must inherit from this.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    def generate_signals(self, market_data: Any) -> Dict[str, float]:
        """
        Analyze market data and return trading signals.
        Returns:
            Dict[symbol, score]: Score typically between -1.0 (Sell) and 1.0 (Buy).
        """
        pass

    @abstractmethod
    def get_risk_factor(self) -> float:
        """
        Get current risk assessment from this engine.
        Returns:
            float: 0.0 (Safe) to 1.0 (Extreme Risk).
        """
        pass
