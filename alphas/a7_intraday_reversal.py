import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A7IntradayReversal(BaseAlpha):
    """
    A7: Intraday Reversal Alpha (Anti-A2)
    Betting against stocks that had strong consistent intraday trends yesterday.
    Logic:
    1. Calculate A2 Score (Trend Quality * Range * Vol)
    2. A7 Score = -1 * A2 Score
    3. Extreme Filter: Only keep scores if Trend Quality is in top 10% (Overheated)
    """
    
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        # 1. Load Features (Same as A2)
        q = market_data.get('intraday_trend_q')
import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A7IntradayReversal(BaseAlpha):
    """
    A7: Intraday Reversal Alpha (Anti-A2)
    Betting against stocks that had strong consistent intraday trends yesterday.
    Logic:
    1. Calculate A2 Score (Trend Quality * Range * Vol)
    2. A7 Score = -1 * A2 Score
    3. Extreme Filter: Only keep scores if Trend Quality is in top 10% (Overheated)
    """
    
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        # 1. Load Features (Same as A2)
        q = market_data.get('intraday_trend_q')
        range_pos = market_data.get('intraday_range_pos')
        vol_rel = market_data.get('intraday_vol_rel')
        
        if q is None or range_pos is None or vol_rel is None:
            return pd.DataFrame()
            
        # Align with universe
        valid_cols = [c for c in universe if c in q.columns]
        q = q[valid_cols]
        range_pos = range_pos[valid_cols]
        vol_rel = vol_rel[valid_cols]
        
        # 2. Calculate Q_t (3-day EMA of Trend Quality)
        Q_t = q.ewm(span=3, adjust=False).mean()
        
        # 3. Scaling (Same as A2)
        scale_range = 0.5 + (range_pos / 2.0)
        scale_vol = 0.5 + (vol_rel.clip(0, 3.0) / 3.0)
        
        # 4. Invert Logic for A7 (Reversal)
        # A2 was: raw_score = Q_t * scale_range * scale_vol
        # A7 is:  raw_score = -1 * Q_t * scale_range * scale_vol
        raw_score = -1.0 * Q_t * scale_range * scale_vol
        
        # 5. Extreme Filter (Phase 4)
        # Only target the top/bottom N% of "Overheating"
        # We use the absolute value of Q_t to measure "Trend Intensity"
        trend_intensity = Q_t.abs()
        
        # Calculate daily quantile threshold (e.g., top 10%)
        # axis=1 means quantile across stocks for each day
        # Relaxed Filter: Top 30% (0.70) instead of 10% (0.90)
        # And Vol > 0.5 instead of 1.0
        daily_threshold = trend_intensity.quantile(0.70, axis=1)
        
        # Create a mask: True if intensity > threshold
        # We align threshold to the dataframe
        is_extreme = trend_intensity.gt(daily_threshold, axis=0)
        
        # Also filter by Volume Pressure (must be significant, e.g., > 1.0)
        is_high_vol = vol_rel > 0.5
        
        # Debug: Check how many signals survive
        # total_signals = raw_score.size
        # survived_signals = (is_extreme & is_high_vol).sum().sum()
        # print(f"DEBUG: A7 Filter Survival Rate: {survived_signals}/{total_signals} ({survived_signals/total_signals:.2%})")
        
        # Apply Filters
        # If not extreme or not high vol, score becomes 0
        filtered_score = raw_score.where(is_extreme & is_high_vol, 0.0)
        
        # 6. Cross-sectional Z-score
        daily_mean = filtered_score.mean(axis=1)
        daily_std = filtered_score.std(axis=1).replace(0, np.nan)
        
        z_score = filtered_score.sub(daily_mean, axis=0).div(daily_std, axis=0)
        
        # 7. Clip and Fill
        final_score = z_score.clip(-3.0, 3.0).fillna(0.0)
        
        # Shift by 1 day to align with trading day
        return final_score.shift(1)
