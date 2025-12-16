import pandas as pd
from typing import Dict, List, Callable, Any
import logging
from .library import trend, volatility, sentiment, flow, momentum

logger = logging.getLogger(__name__)

class FeatureFactory:
    """
    Central engine for calculating market features.
    Ensures consistency between Backtest (Alpha Lab) and Live (Surfing Brain).
    """
    
    def __init__(self):
        self.registry: Dict[str, Callable] = {}
        self._register_defaults()
        logger.info("FeatureFactory initialized with default features.")

    def _register_defaults(self):
        """Register standard library features."""
        # Trend
        self.register_feature('ma_trend', trend.calc_ma_trend)
        self.register_feature('macd', trend.calc_macd)
        self.register_feature('adx', trend.calc_adx)
        
        # Volatility
        self.register_feature('atr', volatility.calc_atr)
        self.register_feature('realized_vol', volatility.calc_realized_vol)
        self.register_feature('bollinger', volatility.calc_bollinger_bands)
        
        # Sentiment
        self.register_feature('news_fear', sentiment.calc_news_fear_score)
        
        # Momentum
        self.register_feature('rsi', momentum.calc_rsi)

        # Flow
        # self.register_feature('investor_flow', flow.calc_investor_flow)

    def register_feature(self, name: str, func: Callable):
        """Register a new feature calculation function."""
        self.registry[name] = func
        logger.debug(f"Registered feature: {name}")

    def compute_features(self, df: pd.DataFrame, config: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Compute requested features for the given DataFrame.
        
        Args:
            df: Input DataFrame (OHLCV)
            config: List of feature configs. 
                    Example: [{'name': 'ma_trend', 'params': {'fast': 20, 'slow': 60}}]
                    Or simple list of names: ['ma_trend', 'atr'] (uses defaults)
            
        Returns:
            DataFrame with added feature columns
        """
        df_out = df.copy()
        
        for item in config:
            if isinstance(item, str):
                name = item
                params = {}
            elif isinstance(item, dict):
                name = item.get('name')
                params = item.get('params', {})
            else:
                continue
                
            if name in self.registry:
                try:
                    # Call function with params
                    df_out = self.registry[name](df_out, **params)
                    logger.debug(f"Computed {name} with params {params}")
                except Exception as e:
                    logger.error(f"Error computing {name}: {e}")
            else:
                logger.warning(f"Feature {name} not found in registry.")
                
        return df_out
