"""
Micro-Regime Classifier
Classifies market state based on Trend and Volatility.
Used by DGE v0.3 to determine Exit Parameters.
"""

import pandas as pd
import numpy as np
from typing import Optional

class MicroRegimeClassifier:
    """
    Classifies market state into Micro-Regimes.
    
    Regimes:
    - Trend: STRONG_UP, WEAK_UP, FLAT, WEAK_DOWN, STRONG_DOWN
    - Volatility: LOW_VOL, MED_VOL, HIGH_VOL
    """
    
    def __init__(self):
        # Thresholds from Research (deep_dive_mechanics_extended.md)
        self.TREND_THRESHOLDS = {
            'STRONG_UP': 0.05,
            'WEAK_UP': 0.01,
            'FLAT': -0.01,
            'WEAK_DOWN': -0.05
            # Below is STRONG_DOWN
        }
        
        self.VOL_THRESHOLDS = {
            'LOW': 0.0251,
            'HIGH': 0.0342
        }
        
    def get_regime(self, daily_df: pd.DataFrame, current_date: pd.Timestamp) -> str:
        """
        Get micro-regime for a specific date.
        
        Args:
            daily_df: Daily DataFrame with 'close', 'high', 'low'
            current_date: Date to classify
            
        Returns:
            str: Micro-regime label (e.g., "STRONG_UP_HIGH_VOL")
        """
        # Find index for date (or previous close)
        # We use 'ffill' to get the latest available data *before* or *at* the current date.
        # Ideally, for intraday trading, we use YESTERDAY's close metrics.
        # But if we are trading today, we might want today's open? 
        # Standard practice: Use T-1 Close metrics for T trading.
        
        # Ensure date is normalized
        target_date = current_date.normalize()
        
        try:
            # Get location
            idx = daily_df.index.get_indexer([target_date], method='ffill')[0]
            
            if idx == -1:
                return "UNKNOWN"
                
            # Calculate Metrics on the fly if not present
            # We need 20 days history
            if idx < 20:
                return "UNKNOWN"
                
            # Slice for calculation (up to this date)
            # Note: If we use 'ffill', idx points to the row.
            # If target_date is today (during trading), and daily_df has today's row (incomplete),
            # we should be careful. Usually daily_df has finished bars.
            # Assuming daily_df contains historical data up to yesterday or today.
            
            row = daily_df.iloc[idx]
            close = row['close']
            
            # Calculate 20-day Return
            # We need close from 20 days ago
            close_20 = daily_df.iloc[idx-20]['close']
            ret_20 = (close - close_20) / close_20
            
            # Calculate ATR 20
            # Need last 20 TRs
            # Simple TR approximation for speed: High - Low (intraday) 
            # Better: Use pre-calculated ATR if available, else calc on fly
            if 'atr_20' in daily_df.columns:
                atr_20 = row['atr_20']
            else:
                # Calc on fly (expensive if done every time, but okay for backtest)
                # Let's assume daily_df is pre-processed or we do a quick calc
                # Quick calc using last 20 rows
                slice_20 = daily_df.iloc[idx-19:idx+1]
                tr = np.maximum(slice_20['high'] - slice_20['low'], 
                                np.abs(slice_20['high'] - slice_20['close'].shift(1))) # Approx
                atr_20 = tr.mean()
                
            vol_ratio = atr_20 / close
            
            # Classify Trend
            if ret_20 > self.TREND_THRESHOLDS['STRONG_UP']: trend = "STRONG_UP"
            elif ret_20 > self.TREND_THRESHOLDS['WEAK_UP']: trend = "WEAK_UP"
            elif ret_20 > self.TREND_THRESHOLDS['FLAT']: trend = "FLAT"
            elif ret_20 > self.TREND_THRESHOLDS['WEAK_DOWN']: trend = "WEAK_DOWN"
            else: trend = "STRONG_DOWN"
            
            # Classify Volatility
            if vol_ratio < self.VOL_THRESHOLDS['LOW']: vol = "LOW_VOL"
            elif vol_ratio > self.VOL_THRESHOLDS['HIGH']: vol = "HIGH_VOL"
            else: vol = "MED_VOL"
            
            return f"{trend}_{vol}"
            
        except Exception as e:
            # print(f"Regime calc error: {e}")
            return "UNKNOWN"
