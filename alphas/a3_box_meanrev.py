import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A3BoxMeanRev(BaseAlpha):
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        """
        Compute Mean Reversion scores:
        Score = -1 * Z-Score(5-day Return)
        
        High Score = Oversold (Buy)
        Low Score = Overbought (Sell)
        """
        # Assuming market_data['daily'] is a DataFrame with MultiIndex (Date, Symbol) or Panel
        # Or dictionary of DataFrames per symbol?
        # Let's assume market_data['daily_close'] is a DataFrame (Index=Date, Columns=Symbols)
        
        closes = market_data.get('daily_close')
        if closes is None or closes.empty:
            return pd.DataFrame()
            
        # Calculate 5-day returns
        returns_5d = closes.pct_change(5)
        
        # Calculate Z-Score (Cross-sectional)
        # (Val - Mean) / Std
        mean_ret = returns_5d.mean(axis=1)
        std_ret = returns_5d.std(axis=1)
        
        z_scores = returns_5d.sub(mean_ret, axis=0).div(std_ret, axis=0)
        
        # Invert for Mean Reversion (Oversold -> High Score)
        alpha_scores = -1 * z_scores
        
        # Normalize to 0~1 or -1~1?
        # Champion Rule expects positive scores for ranking?
        # Or just relative ranking?
        # Let's keep it raw Z-score for now, but maybe clip to -3~3
        # Normalize Z-score to 0-100 scale
        # Z=-3 -> 0, Z=0 -> 50, Z=+3 -> 100
        alpha_scores = ((alpha_scores.clip(-3, 3) + 3) / 6) * 100
        
        return alpha_scores.fillna(50)
