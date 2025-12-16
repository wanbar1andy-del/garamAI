"""
Multi-Factor Strategy (US_MULTI_MVQL)
Composite strategy combining Momentum, Value, Quality, and Low Volatility.
"""

from typing import Dict
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.us_academic.strategies.base_factor_strategy import BaseFactorStrategy
from alpha_lab.us_academic.academic_factors import (
    calc_momentum,
    calc_value_factors,
    calc_quality_factors,
    calc_low_vol_factor,
    rank_cross_sectional,
    calc_composite_factor
)

class MultiFactorStrategy(BaseFactorStrategy):
    """
    US_MULTI_MVQL: Multi-Factor Composite Strategy
    
    Combines: Momentum + Value + Quality + Low Volatility
    Long: Top 20% by composite score
    Short: Bottom 20% by composite score
    Rebalance: Monthly
    """
    
    def __init__(self, account, config=None):
        if config is None:
            config = {
                'rebalance_freq': 'M',
                'long_only': False,
                'long_quantile': 0.8,  # Top 20%
                'short_quantile': 0.2,  # Bottom 20%
                'weights': {
                    'momentum': 0.25,
                    'value': 0.25,
                    'quality': 0.25,
                    'low_vol': 0.25
                }
            }
        
        super().__init__(account, config, "US_MULTI_MVQL")
        
        self.weights = config.get('weights', {
            'momentum': 0.25,
            'value': 0.25,
            'quality': 0.25,
            'low_vol': 0.25
        })
        
    def calculate_scores(self, prices: pd.DataFrame) -> pd.Series:
        """Calculate composite factor scores"""
        # Calculate individual factors
        momentum = calc_momentum(prices, lookback=252, skip=21)
        low_vol = calc_low_vol_factor(prices, window=60)
        
        # Value and Quality (mock for now)
        value_df = calc_value_factors(prices)
        value_score = calc_composite_factor(value_df)
        
        symbols = list(prices.columns)
        quality_df = calc_quality_factors(symbols=symbols)
        quality_score = calc_composite_factor(quality_df)
        
        # Rank each factor (0-1 scale)
        momentum_rank = rank_cross_sectional(momentum, ascending=True)
        low_vol_rank = rank_cross_sectional(low_vol, ascending=True)
        value_rank = rank_cross_sectional(value_score, ascending=True)
        quality_rank = rank_cross_sectional(quality_score, ascending=True)
        
        # Combine with weights
        composite = (
            self.weights['momentum'] * momentum_rank.fillna(0.5) +
            self.weights['value'] * value_rank.fillna(0.5) +
            self.weights['quality'] * quality_rank.fillna(0.5) +
            self.weights['low_vol'] * low_vol_rank.fillna(0.5)
        )
        
        return composite
    
    def get_expected_metrics(self) -> Dict[str, tuple]:
        """Expected performance metrics"""
        return {
            'sharpe': (0.7, 1.3),
            'max_dd': (-0.22, -0.12),
            'annual_return': (0.10, 0.18)
        }
