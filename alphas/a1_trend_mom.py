import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A1TrendMom6m(BaseAlpha):
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        """
        Compute 6-Month Trend Momentum scores.
        
        Logic:
        - Calculate 6-month (approx 120 days) price return.
        - Normalize cross-sectionally to 0-100 scale.
        - Higher score = Stronger Upward Trend.
        
        Rationale:
        - Primary engine for Trend Regimes (R1, R2).
        - Captures medium-term momentum persistence.
        """
        closes = market_data.get('daily_close')
        
        if closes is None or closes.empty:
            return pd.DataFrame()
            
        # 1. Calculate 6-Month Return (120 trading days)
        # Using 120 days as approximation for 6 months
        momentum_6m = closes.pct_change(120)
        
        # 2. Cross-sectional Ranking (Percentile)
        # We want a 0-100 score where 100 is the highest momentum.
        # rank(pct=True) returns 0.0 to 1.0
        scores = momentum_6m.rank(axis=1, pct=True) * 100
        
        # 3. Optional: Absolute Momentum Filter
        # If return is negative, cap score at 40 (Neutral/Sell) regardless of rank?
        # For now, let's keep it pure relative strength but maybe penalize negative returns.
        
        # Simple penalty for negative absolute return
        # If return < 0, score = score * 0.5 (Push towards sell)
        mask_negative = momentum_6m < 0
        scores[mask_negative] = scores[mask_negative] * 0.5
        
        return scores.fillna(0)
