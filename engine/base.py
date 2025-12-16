from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class BaseEngine(ABC):
    """
    Abstract Base Class for GARAM Trading Engines.
    Enforces a consistent interface for signal generation and risk assessment.
    """

    @abstractmethod
    def analyze(self, date: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signals.

        Args:
            date: Target date for validation/logging.
            context: Dictionary containing market data, indices, etc.
                     e.g. {'market_data': df_map, 'regime': 'R3_UP_BOX', ...}

        Returns:
            Dict containing:
            - 'signals': Dict[str, float]  # Symbol -> Score (0.0 to 100.0)
            - 'meta': Dict[str, Any]       # Engine-specific metadata (e.g. Regime, MacroScore)
            - 'directives': Dict[str, Any] # Special requests (e.g. 'TURBO', 'LIQUIDATE')
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return engine name for logging."""
        pass
