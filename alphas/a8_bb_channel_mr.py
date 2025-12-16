import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A8BBChannelMR(BaseAlpha):
    """
    A8: Narrow BB Mean Reversion (Experiment)
    
    Logic:
    1. Calculate Bollinger Bands (N, K) from config (Default: 20, 1.0)
    2. Calculate %b = (Close - Lower) / (Upper - Lower)
    3. Raw Score = -((%b - 0.5).clip(-2, 2))
       - If %b > 0.5 (Upper Half), Score < 0 (Short/Avoid)
       - If %b < 0.5 (Lower Half), Score > 0 (Long)
       - The further from Mid, the stronger the signal.
    4. Cross-sectional Z-score
    """
    
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        # 1. Load Data
        close = market_data.get('daily_close')
        
        if close is None:
            return pd.DataFrame()
            
        # Align with universe
        valid_cols = [c for c in universe if c in close.columns]
        close = close[valid_cols]
        
        # 2. Parameters
        params = self.config.get('params', {})
        window = params.get('bb_period', 20)
        k = params.get('bb_k', 1.0)
        
        # 3. Calculate Bollinger Bands
        mid = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        
        upper = mid + k * std
        lower = mid - k * std
        
        # Band Width (for denominator)
        band_width = upper - lower
        band_width = band_width.replace(0, np.nan)
        
        # 4. Calculate %b
        # pct_b = (close - lower) / (upper - lower)
        pct_b = (close - lower) / band_width
        
        # 5. Raw Score (Mean Reversion)
        # Center at 0.5 (Mid Band)
        # If pct_b = 1.0 (Upper), diff = 0.5 -> Score = -0.5 (Short)
        # If pct_b = 0.0 (Lower), diff = -0.5 -> Score = +0.5 (Long)
        # We want to amplify this.
        # Clip to avoid extreme outliers (e.g. pct_b = 10.0)
        
        raw_score = -((pct_b - 0.5).clip(-2.0, 2.0))
        
        # 6. Cross-sectional Z-score (Standardize)
        daily_mean = raw_score.mean(axis=1)
        daily_std = raw_score.std(axis=1).replace(0, np.nan)
        
        z_score = raw_score.sub(daily_mean, axis=0).div(daily_std, axis=0)
        
        # 7. Final Clip and Shift
        final_score = z_score.clip(-3.0, 3.0).fillna(0.0)
        
        return final_score.shift(1)
