"""
Market Regime Detection Module
Classifies market states into Green (Eat), Yellow (Hurt), and Red (Death).
"""

from enum import Enum
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

class MarketState(Enum):
    GREEN = "GREEN"   # Eat: Low Risk, High Opportunity (Uptrend + Low Vol)
    YELLOW = "YELLOW" # Hurt: Ambiguous/Choppy (Sideways or High Vol Uptrend)
    RED = "RED"       # Death: High Risk (Downtrend + High Vol)

@dataclass
class RegimeMetrics:
    state: MarketState
    trend_score: float      # 1.0 (Strong Up) to -1.0 (Strong Down)
    volatility_score: float # 0.0 (Low) to 1.0 (High)
    ma_200_dist: float      # % distance from MA200
    atr_percentile: float   # Current ATR percentile (0-1)

class MarketRegimeDetector:
    """
    Detects market regime based on Trend and Volatility.
    
    Logic:
    1. Trend: Price vs SMA200, SMA50 vs SMA200
    2. Volatility: ATR percentile (vs 1-year history)
    
    Classification:
    - GREEN: Price > SMA200 AND Volatility < 50th percentile
    - RED: Price < SMA200 AND Volatility > 80th percentile
    - YELLOW: All other cases
    """
    
    def __init__(self, window_slow: int = 200, window_fast: int = 50, vol_window: int = 20):
        self.window_slow = window_slow
        self.window_fast = window_fast
        self.vol_window = vol_window
        
    def compute_regime(self, prices: pd.Series, high: pd.Series = None, low: pd.Series = None, close: pd.Series = None) -> pd.DataFrame:
        """
        Compute regime for the entire history.
        Returns DataFrame with columns: ['state', 'trend', 'volatility', 'regime_code']
        """
        # If OHLC not provided, assume prices is Close
        if close is None:
            close = prices
        if high is None:
            high = prices
        if low is None:
            low = prices
            
        df = pd.DataFrame(index=prices.index)
        df['close'] = close
        
        # 1. Trend Components
        df['sma_slow'] = df['close'].rolling(window=self.window_slow).mean()
        df['sma_fast'] = df['close'].rolling(window=self.window_fast).mean()
        
        # Distance from SMA200 (%)
        df['ma_dist'] = (df['close'] - df['sma_slow']) / df['sma_slow']
        
        # 2. Volatility Components (ATR)
        # Calculate TR
        prev_close = df['close'].shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        df['atr'] = tr.rolling(window=self.vol_window).mean()
        
        # ATR Percentile (Rolling 1 year = 252 days)
        df['atr_pct'] = df['atr'].rolling(window=252).rank(pct=True)
        
        # 3. Classification Logic
        def classify(row):
            if pd.isna(row['sma_slow']) or pd.isna(row['atr_pct']):
                return None
                
            # GREEN: Uptrend + Low Vol
            if row['close'] > row['sma_slow'] and row['atr_pct'] < 0.5:
                return MarketState.GREEN.value
            
            # RED: Downtrend + High Vol
            elif row['close'] < row['sma_slow'] and row['atr_pct'] > 0.8:
                return MarketState.RED.value
                
            # YELLOW: Everything else
            else:
                return MarketState.YELLOW.value
                
        df['state'] = df.apply(classify, axis=1)
        
        # Map to integer code for plotting/ML: Green=1, Yellow=0, Red=-1
        state_map = {
            MarketState.GREEN.value: 1,
            MarketState.YELLOW.value: 0,
            MarketState.RED.value: -1,
            None: 0
        }
        df['regime_code'] = df['state'].map(state_map)
        
        return df[['state', 'ma_dist', 'atr_pct', 'regime_code']]
    
    def get_current_state(self, prices: pd.Series, high: pd.Series = None, low: pd.Series = None, close: pd.Series = None) -> Optional[RegimeMetrics]:
        """Get the regime state for the latest data point"""
        df = self.compute_regime(prices, high, low, close)
        last_row = df.iloc[-1]
        
        if pd.isna(last_row['state']):
            return None
            
        return RegimeMetrics(
            state=MarketState(last_row['state']),
            trend_score=last_row['ma_dist'], # Proxy for trend strength
            volatility_score=last_row['atr_pct'],
            ma_200_dist=last_row['ma_dist'],
            atr_percentile=last_row['atr_pct']
        )
