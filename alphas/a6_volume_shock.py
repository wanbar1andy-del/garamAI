import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A6VolumeShock(BaseAlpha):
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        """
        Compute Volume Shock Reversal scores:
        
        Logic:
        - Calculate Volume Ratio (Volume / 20-day MA Volume).
        - Calculate 5-day Price Return.
        - Score = -1 * (Price Return * Volume Ratio)
        
        Rationale:
        - Captures "Panic Selling" (Price Drop + High Volume) -> High Score (Buy).
        - Captures "Buying Climax" (Price Spike + High Volume) -> Low Score (Sell).
        - Works best in Mean Reversion regimes (Box/Chop).
        """
        closes = market_data.get('daily_close')
        volumes = market_data.get('daily_volume')
        
        if closes is None or volumes is None:
            return pd.DataFrame()
            
        # 1. Volume Shock (Ratio vs 20d MA)
        vol_ma_20 = volumes.rolling(window=20).mean()
        vol_ratio = volumes / vol_ma_20
        
        # Cap extreme volume shocks to avoid skewing (e.g., max 5x)
        vol_ratio = vol_ratio.clip(0, 5)
        
        # 2. Price Shock (5-day Return)
        ret_5d = closes.pct_change(5)
        
        # 3. Reversal Score
        # We want to buy when Price is DOWN and Volume is UP.
        # Score = -1 * Return * Volume_Ratio
        # Example: Ret = -0.1 (Drop), Vol = 2.0 -> Score = -1 * -0.1 * 2.0 = +0.2 (Good)
        raw_score = -1 * ret_5d * vol_ratio
        
        # 4. Cross-sectional Ranking (Z-score)
        mean_s = raw_score.mean(axis=1)
        std_s = raw_score.std(axis=1)
        
        z_scores = raw_score.sub(mean_s, axis=0).div(std_s, axis=0)
        
        # Normalize Z-score to 0-100 scale
        # Z=-3 -> 0, Z=0 -> 50, Z=+3 -> 100
        alpha_scores = ((z_scores.clip(-3, 3) + 3) / 6) * 100
        
        return alpha_scores.fillna(50)
