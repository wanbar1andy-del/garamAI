"""
Low Volatility Strategy (US_LOWVOL)
Long-only low volatility strategy.
"""

from typing import Dict
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.us_academic.strategies.base_factor_strategy import BaseFactorStrategy
from alpha_lab.us_academic.academic_factors import calc_low_vol_factor

class LowVolStrategy(BaseFactorStrategy):
    """
    US_LOWVOL: Low Volatility Strategy
    
    Long: Top 30% by low volatility score
    Short: None (long-only)
    Rebalance: Monthly
    """
    
    def __init__(self, account, config=None):
        if config is None:
            config = {
                'rebalance_freq': 'M',
                'long_only': True,
                'long_quantile': 0.7,  # Top 30%
                'short_quantile': 0.0,  # No shorts
                'window': 60  # 60-day volatility
            }
        
        super().__init__(account, config, "US_LOWVOL")
        
        self.window = config.get('window', 60)
        
    def calculate_scores(self, prices: pd.DataFrame) -> pd.Series:
        """Calculate low volatility scores"""
        return calc_low_vol_factor(
            prices,
            window=self.window,
            method='std'
        )
    
    def get_expected_metrics(self) -> Dict[str, tuple]:
        """Expected performance metrics"""
        return {
            'sharpe': (0.6, 1.2),
            'max_dd': (-0.20, -0.10),
            'annual_return': (0.06, 0.12)
        }
