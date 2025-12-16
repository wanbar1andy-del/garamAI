import pandas as pd
from abc import ABC, abstractmethod

class BaseAlpha(ABC):
    def __init__(self, alpha_id: str, config: dict):
        self.alpha_id = alpha_id
        self.config = config
        self.name = config.get('name', alpha_id)
        self.regimes = config.get('regimes', {}).get('include', [])

    @abstractmethod
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        """
        Compute alpha scores for the given universe.
        
        Args:
            market_data: Dictionary containing market data (e.g., {'minute': ..., 'daily': ...})
            universe: List of symbols to score
            
        Returns:
            pd.DataFrame: Index=Date, Columns=Symbols, Values=Score
            Or Series if single date? 
            Let's assume it returns a DataFrame aligned with market_data dates.
        """
        pass
    
    def is_active(self, regime: str) -> bool:
        """Check if alpha should be active in the current regime."""
        if not self.regimes:
            return True
        return regime in self.regimes
