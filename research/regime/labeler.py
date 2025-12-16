import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class RegimeProfile:
    name: str
    description: str
    criteria: str

class RegimeLabeler:
    """
    Identifies market regimes based on historical price data.
    """
    def __init__(self):
        self.regimes = {
            'BULL_LOW_VOL': RegimeProfile('BULL_LOW_VOL', 'Steady Uptrend', 'Price > MA200 & Vol < Threshold'),
            'BULL_HIGH_VOL': RegimeProfile('BULL_HIGH_VOL', 'Volatile Uptrend', 'Price > MA200 & Vol > Threshold'),
            'BEAR_LOW_VOL': RegimeProfile('BEAR_LOW_VOL', 'Steady Downtrend', 'Price < MA200 & Vol < Threshold'),
            'BEAR_HIGH_VOL': RegimeProfile('BEAR_HIGH_VOL', 'Panic/Crash', 'Price < MA200 & Vol > Threshold'),
            'CRISIS': RegimeProfile('CRISIS', 'Extreme Stress', 'Drawdown > 20% & Vol > Extreme')
        }

    def calculate_features(self, df: pd.DataFrame, price_col='close') -> pd.DataFrame:
        """
        Calculate regime features: Trend (MA200), Volatility (ATR/Std), Drawdown.
        """
        df = df.copy()
        
        # Trend
        df['ma_200'] = df[price_col].rolling(window=200).mean()
        df['trend_signal'] = np.where(df[price_col] > df['ma_200'], 1, -1)
        
        # Volatility (Annualized StdDev of daily returns)
        df['returns'] = df[price_col].pct_change()
        df['vol_20'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # Drawdown
        df['rolling_max'] = df[price_col].rolling(window=252, min_periods=1).max()
        df['drawdown'] = (df[price_col] - df['rolling_max']) / df['rolling_max']
        
        return df

    def label_regimes(self, df: pd.DataFrame, vol_threshold=0.15, crisis_threshold=0.30) -> pd.DataFrame:
        """
        Apply rules to label regimes.
        """
        df = self.calculate_features(df)
        
        conditions = [
            (df['drawdown'] < -0.20) & (df['vol_20'] > crisis_threshold), # CRISIS
            (df['trend_signal'] == 1) & (df['vol_20'] <= vol_threshold),  # BULL_LOW_VOL
            (df['trend_signal'] == 1) & (df['vol_20'] > vol_threshold),   # BULL_HIGH_VOL
            (df['trend_signal'] == -1) & (df['vol_20'] <= vol_threshold), # BEAR_LOW_VOL
            (df['trend_signal'] == -1) & (df['vol_20'] > vol_threshold)   # BEAR_HIGH_VOL
        ]
        
        choices = [
            'CRISIS',
            'BULL_LOW_VOL',
            'BULL_HIGH_VOL',
            'BEAR_LOW_VOL',
            'BEAR_HIGH_VOL'
        ]
        
        df['regime'] = np.select(conditions, choices, default='UNCERTAIN')
        return df
