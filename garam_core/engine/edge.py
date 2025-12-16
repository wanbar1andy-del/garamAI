# garam_core/engine/edge.py
from __future__ import annotations
import numpy as np
import pandas as pd


def _z(x: pd.Series, n: int) -> pd.Series:
    m = x.rolling(n).mean()
    s = x.rolling(n).std()
    return (x - m) / (s.replace(0, np.nan))


def edge_score(ohlcv: pd.DataFrame) -> float:
    """
    Returns edge_score in [0, 1].
    Uses only recent window; deterministic.
    """
    if len(ohlcv) < 60:
        return 0.5 # Neutral fallback for warmup

    c = ohlcv["close"]
    v = ohlcv["volume"] if "volume" in ohlcv.columns else None

    r1 = c.pct_change()
    mom = r1.rolling(30).sum()                      # 30분 누적 모멘텀
    acc = mom.diff(10)                              # 모멘텀 가속
    vol = r1.rolling(60).std()                      # 60분 변동성

    # We need n=240 bars for Z-score, if not enough, use what we have or min_periods
    min_p = 60
    
    # Calculate components
    # Handle potentially short history gracefully if needed, but standard logic assumes sufficient window passed
    if len(c) < 240:
        # Fallback or simplified calculation if data is short?
        # User script passed 20000 bars, so usually fine.
        pass

    mom_z = _z(mom, 240).iloc[-1]
    acc_z = _z(acc, 240).iloc[-1]
    vol_z = _z(vol, 240).iloc[-1]
    
    # Check for NaN (warmup)
    if np.isnan(mom_z) or np.isnan(acc_z) or np.isnan(vol_z):
        return 0.5

    # volume shock (optional)
    if v is not None:
        vs = _z(v, 240).iloc[-1]
        if np.isnan(vs): vs = 0.0
    else:
        vs = 0.0

    # 엣지 구성: 추세+가속은 +, 변동성 과도는 -
    raw = 0.9 * np.tanh(mom_z) + 0.6 * np.tanh(acc_z) - 0.4 * np.tanh(vol_z) + 0.2 * np.tanh(vs)

    # 0~1 스케일
    s = 0.5 + 0.5 * np.tanh(raw)
    return float(np.clip(s, 0.0, 1.0))
