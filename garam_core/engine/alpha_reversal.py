# garam_core/engine/alpha_reversal.py
from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class AlphaA7Params:
    heat_window: int = 60
    heat_quantile: float = 0.70  # Top 30%
    pressure_threshold: float = 0.5
    
    # Filter calculation
    vwap_window: int = 120

def _calc_volume_pressure(df: pd.DataFrame, n: int = 10) -> float:
    # Approximate Buy Volume using Close > Open
    # If C > O: Buy Vol = Vol
    # If C < O: Sell Vol = Vol
    # Else: Neutral
    # Pressure = Buy Vol / Total Vol (last n bars)
    
    close = df["close"].tail(n)
    open_ = df["open"].tail(n)
    vol = df["volume"].tail(n)
    
    buy_vol = vol[close > open_].sum()
    total_vol = vol.sum()
    
    if total_vol == 0:
        return 0.5
    return buy_vol / total_vol

def _calc_heat_rank(df: pd.DataFrame, window: int) -> float:
    # Heat: Deviation from moving average normalized by volatility
    c = df["close"]
    if len(c) < window:
        return 0.0
        
    ma = c.rolling(window).mean()
    std = c.rolling(window).std()
    
    z = (c - ma) / std
    # Rank: simple z-score percentile approx or just return z-score and user sets threshold?
    # User said "Top 30% Heat". 
    # Let's assume this means relative to recent history or absolute Z threshold?
    # "Normalized Heat Rank >= 0.70" suggests a 0..1 score.
    # Let's use Percentile Rank over rolling window.
    
    z_recent = z.tail(window)
    current_z = float(z.iloc[-1])
    
    # Percentile of current Z within last window Z's
    rank = (z_recent < current_z).mean()
    return float(rank)

def decide_alpha_a7(
    ohlcv_window: pd.DataFrame,
    params: AlphaA7Params
) -> Dict[str, Any]:
    """
    Returns Alpha A7 signal state.
    Condition: Heat Rank >= 0.70 AND Volume Pressure > 0.5
    """
    heat_rank = _calc_heat_rank(ohlcv_window, params.heat_window)
    vol_pressure = _calc_volume_pressure(ohlcv_window, 10) # 10-bar pressure
    
    signal = False
    if heat_rank >= params.heat_quantile and vol_pressure > params.pressure_threshold:
        signal = True
        
    return {
        "signal": signal,
        "heat_rank": heat_rank,
        "vol_pressure": vol_pressure,
        "reason": "Top 30% Heat & High Vol Pressure" if signal else ""
    }
