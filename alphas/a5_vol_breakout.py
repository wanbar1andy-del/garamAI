import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A5VolBreakout(BaseAlpha):
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        """
        Compute Short-term Volatility Breakout scores:
        
        Logic:
        - Calculate 5-day Price Change.
        - Calculate 5-day Range (High - Low) or ATR as volatility measure.
        - Score = (Close - Close_5d) / (Average Range_5d)
        
        Rationale:
        - Measures "Efficiency of Movement".
        - High score means price moved significantly relative to its recent noise level.
        - This is a "Breakout" signal, effective in R1/R2.
        """
        closes = market_data.get('daily_close')
        highs = market_data.get('daily_high')
        lows = market_data.get('daily_low')
        
        if closes is None or highs is None or lows is None:
            return pd.DataFrame()
            
        # 1. 5-day Momentum
        mom_5d = closes.diff(5)
        
        # 2. 5-day Volatility (Average Daily Range)
        daily_range = highs - lows
        vol_5d = daily_range.rolling(window=5).mean()
        
        # Avoid division by zero
        vol_5d = vol_5d.replace(0, np.nan)
        
        # 3. Volatility Adjusted Momentum
        # (Price Change) / (Volatility)
        # Similar to Sharpe Ratio but using Range instead of StdDev
        vam_5d = mom_5d / vol_5d
        
        # 4. Cross-sectional Ranking (Z-score)
        mean_vam = vam_5d.mean(axis=1)
        std_vam = vam_5d.std(axis=1)
        
        z_scores = vam_5d.sub(mean_vam, axis=0).div(std_vam, axis=0)
        
        # Normalize Z-score to 0-100 scale (Spec Requirement)
        # Z=-3 -> 0, Z=0 -> 50, Z=+3 -> 100
        alpha_scores = ((z_scores.clip(-3, 3) + 3) / 6) * 100
        
        return alpha_scores.fillna(50) # Neutral if NaN
