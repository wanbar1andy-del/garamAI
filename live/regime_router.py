import pandas as pd
import numpy as np

class RegimeRouter:
    """
    Determines the current market regime based on technical indicators.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.ma_fast = self.config.get('ma_fast', 20)
        self.ma_slow = self.config.get('ma_slow', 60)
        self.vol_window = self.config.get('vol_window', 20)
        
    def get_regime(self, df: pd.DataFrame) -> str:
        """
        Calculates regime from the provided DataFrame.
        Expects 'close' column and sufficient history.
        """
        if len(df) < self.ma_slow:
            return "UNKNOWN"
            
        # Calculate Indicators
        ma_fast_val = df['close'].rolling(window=self.ma_fast).mean().iloc[-1]
        ma_slow_val = df['close'].rolling(window=self.ma_slow).mean().iloc[-1]
        
        # Simple Trend Logic
        if ma_fast_val > ma_slow_val:
            # Check Volatility for "YELLOW" vs "GREEN"
            # For now, simple Bull/Bear
            return "GREEN"
        else:
            return "RED"
            
    def get_regime_details(self, df: pd.DataFrame) -> dict:
        regime = self.get_regime(df)
        return {
            'regime': regime,
            'ma_fast': df['close'].rolling(window=self.ma_fast).mean().iloc[-1],
            'ma_slow': df['close'].rolling(window=self.ma_slow).mean().iloc[-1],
            'last_close': df['close'].iloc[-1]
        }
