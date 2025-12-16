"""
US Academic Factor Strategies Package
"""
from .base_factor_strategy import BaseFactorStrategy
from .momentum_strategy import MomentumStrategy
from .low_vol_strategy import LowVolStrategy
from .multi_factor_strategy import MultiFactorStrategy

__all__ = [
    'BaseFactorStrategy',
    'MomentumStrategy',
    'LowVolStrategy',
    'MultiFactorStrategy'
]
