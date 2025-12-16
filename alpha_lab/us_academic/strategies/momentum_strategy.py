"""
Momentum Strategy (US_MOM_12_1)
Long-short momentum strategy based on 12-month returns (excluding recent 1 month).
"""

from typing import Dict
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.us_academic.strategies.base_factor_strategy import BaseFactorStrategy
from alpha_lab.us_academic.academic_factors import calc_momentum

class MomentumStrategy(BaseFactorStrategy):
    """
    US_MOM_12_1: Momentum Strategy
    
    Long: Top 20% by 12-month momentum
    Short: Bottom 20% by 12-month momentum
    Rebalance: Monthly
    """
    
    def __init__(self, account, config=None):
        if config is None:
            config = {
                'rebalance_freq': 'M',
                'long_only': False,
                'long_quantile': 0.8,  # Top 20%
                'short_quantile': 0.2,  # Bottom 20%
                'lookback': 252,  # 12 months
                'skip': 21  # Skip recent 1 month
            }
        
        super().__init__(account, config, "US_MOM_12_1")
        
        self.lookback = config.get('lookback', 252)
        self.skip = config.get('skip', 21)
        
    def calculate_scores(self, prices: pd.DataFrame) -> pd.Series:
        """Calculate momentum scores"""
        return calc_momentum(
            prices,
            lookback=self.lookback,
            skip=self.skip,
            method='total_return'
        )
    
    def get_expected_metrics(self) -> Dict[str, tuple]:
        """Expected performance metrics"""
        return {
            'sharpe': (0.5, 1.0),
            'max_dd': (-0.25, -0.15),
            'annual_return': (0.08, 0.15)
        }
