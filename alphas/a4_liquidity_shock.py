import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A4LiquidityShock(BaseAlpha):
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        """
        Compute Liquidity Shock scores:
        1. Volume Spike: Volume / MA(Volume, 20)
        2. Price Resilience: (Close - Open) / Open > 0
        
        Score = Volume Ratio (if resilient) else 0
        """
        closes = market_data.get('daily_close')
        opens = market_data.get('daily_open')
        volumes = market_data.get('daily_volume')
        
        if closes is None or volumes is None:
            return pd.DataFrame()
            
        # 1. Volume Spike
        vol_ma20 = volumes.rolling(window=20).mean()
        vol_ratio = volumes.div(vol_ma20)
        
        # 2. Price Resilience (Intraday Strength)
        # Using daily bars for now
        is_resilient = closes > opens
        
        # Combine
        # If resilient, score = vol_ratio. Else 0 (or negative?)
        # Let's say 0 for now.
        
        alpha_scores = vol_ratio.where(is_resilient, 0)
        
        # Normalize?
        # Volume spikes can be huge (10x).
        # Let's clip to 5.
        alpha_scores = alpha_scores.clip(0, 5)
        
        return alpha_scores
