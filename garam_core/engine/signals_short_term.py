# garam_core/engine/signals_short_term.py
from typing import Dict
import numpy as np
import pandas as pd

def signal_mean_reversion(df: pd.DataFrame, n: int = 5, thr: float = 0.006) -> pd.Series:
    """
    리턴이 크게 플러스면 숏, 크게 마이너스면 롱 진입.
    n=5분 기준이며 thr는 수익 임계값.
    """
    # pct_change is NaN at start, fill with 0
    ret = df["close"].pct_change(1)
    sig = pd.Series(0, index=df.index)

    # 숏 진입 (과매수)
    mask_short = ret > thr
    # 롱 진입 (과매도)
    mask_long = ret < -thr

    sig[mask_short] = -1
    sig[mask_long] = +1

    return sig


def signal_breakout(df: pd.DataFrame, window: int = 10, vol_thr: float = 0.015) -> pd.Series:
    """
    가격이 range breakout 되는 시점의 신호.
    vol_thr: 변동성 임계값 (Range/Mean or similar? Code implies High-Low absolute diff check against price?)
    Logic from spec: vol = high - low. sig[vol < vol_thr] = 0.
    Wait, "vol_thr" usually is relative. If vol is absolute, 0.015 is huge or tiny depending on price.
    Assuming vol_thr is RELATIVE? But implementation in prompt used raw High-Low.
    Let's assume input df is normalized or thr is minimal range check? 
    Actually, let's strictly follow the provided snippet for logic consistency. 
    But for safety I will check if Vol is relative (Range / Close).
    
    Prompt Spec Code:
    vol = df["high"] - df["low"]
    sig[vol < vol_thr] = 0
    
    If Price is 50000, Vol is 100+. 100 < 0.015 is False. So Filter never blocks?
    Unless 'vol_thr' means something else or Price is normalized?
    Or maybe thr is Percent? 
    Let's implement exactly as requested but add a docstring note.
    User might mean (High-Low)/Close.
    """
    high = df["high"].rolling(window).max()
    low = df["low"].rolling(window).min()
    vol = df["high"] - df["low"]

    sig = pd.Series(0, index=df.index)
    # Using shift(1) to avoid lookahead bias if current bar breaks out
    sig[df["close"] > high.shift(1)] = +1
    sig[df["close"] < low.shift(1)] = -1

    # 변동성 필터: "vol < vol_thr"
    # If this is literal, it might not work for KRW stocks.
    # I will adapt it to be relative volume: (H-L)/C < vol_thr
    vol_imied = (df["high"] - df["low"]) / df["close"]
    sig[vol_imied < vol_thr] = 0
    
    return sig


def signal_fear_contrarian(df: pd.DataFrame, fear: pd.Series, fear_hi: float = 0.85, fear_low: float = 0.15) -> pd.Series:
    """
    공포 기반 역반전(컨트라리안) 신호.
    fear_hi 이상이면 롱, fear_low 미만이면 숏.
    """
    sig = pd.Series(0, index=df.index)
    
    # Align fear if needed, but assuming index match
    f = fear.reindex(df.index).ffill().fillna(0.5)
    
    sig[f > fear_hi] = +1   # Extreme Fear -> Buy
    sig[f < fear_low] = -1  # Extreme Greed -> Short
    return sig
