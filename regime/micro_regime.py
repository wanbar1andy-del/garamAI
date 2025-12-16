"""
Micro Regime Logic Module
Shared by Analysis, Backtest, and Live Trading.
"""

import pandas as pd
import numpy as np

def calculate_trend_score(ret_5d: float, atr_pct: float) -> float:
    """
    Calculate a normalized trend score (-1.0 to 1.0) based on 5-day return and volatility.
    """
    # Normalize return: 5% move = 1.0 score (approx)
    score = ret_5d / 0.05
    
    # Volatility penalty? Or just use return for direction?
    # Let's keep it simple: Directional Score.
    # Cap at +/- 1.5
    score = max(min(score, 1.5), -1.5)
    return score

def classify_micro_regime(one_day_ret: float, five_day_ret: float, atr_pct: float) -> str:
    """
    Score-based micro-regime classification (R1~R7).
    """
    score = calculate_trend_score(five_day_ret, atr_pct)
    
    # R1: Strong Up (>= 0.8)
    if score >= 0.8: return "R1_STRONG_UP"
    
    # R2: Up (0.5 ~ 0.8)
    if score >= 0.5: return "R2_UP"
    
    # R3: Up-Box (0.2 ~ 0.5)
    if score >= 0.2: return "R3_UP_BOX"
    
    # R4: Box (-0.2 ~ 0.2)
    if score > -0.2: return "R4_BOX"
    
    # R5: Down-Box (-0.5 ~ -0.2)
    if score > -0.5: return "R5_DOWN_BOX"
    
    # R6: Down (-0.8 ~ -0.5)
    if score > -0.8: return "R6_DOWN"
    
    # R7: Crash (<= -0.8)
    return "R7_CRASH"

def calculate_latest_micro_regime(history_df: pd.DataFrame) -> str:
    """
    Calculate the micro regime based on the latest available data (Yesterday's Close).
    """
    if len(history_df) < 20:
        return "R4_BOX" # Default to Box if unknown
        
    df = history_df.copy()
    
    # 1. Returns
    close = df['close']
    ret_1d = close.pct_change(1).iloc[-1]
    ret_5d = close.pct_change(5).iloc[-1]
    
    # 2. ATR
    high = df['high']
    low = df['low']
    prev_close = close.shift(1)
    
    tr = np.maximum(high - low, np.maximum(abs(high - prev_close), abs(low - prev_close)))
    atr = tr.rolling(14).mean()
    atr_pct = (atr / close).iloc[-1]
    
    if pd.isna(ret_1d) or pd.isna(ret_5d) or pd.isna(atr_pct):
        return "R4_BOX"
        
    return classify_micro_regime(ret_1d, ret_5d, atr_pct)
