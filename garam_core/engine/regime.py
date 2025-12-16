# garam_core/engine/regime.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any, Optional
import pandas as pd


Regime = Literal["BULL", "BEAR", "NEUTRAL"]


@dataclass(frozen=True)
class RegimeParams:
    """
    Contract Notes
    - All thresholds are expressed as fractional buffers (e.g., 0.01 = +1%).
    - MA windows are in bars (daily/minute both supported as long as df index is DatetimeIndex).
    """
    ma_fast: int = 20
    ma_slow: int = 60
    bull_buffer: float = 0.00   # Ts
    bear_buffer: float = 0.00   # Ws

    # Optional confidence shaping
    min_ma_slope: float = 0.0   # require MA_fast slope > this to be BULL


def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def classify_regime(
    market_df: pd.DataFrame,
    params: RegimeParams,
) -> Dict[str, Any]:
    """
    PURPOSE
      Decide market regime only (no position / no leverage).

    INPUT CONTRACT
      - market_df must already pass Gate1 (schema): tz-aware datetime index, sorted.
      - columns: open, high, low, close, volume

    OUTPUT CONTRACT
      {
        "regime": "BULL"|"BEAR"|"NEUTRAL",
        "confidence": float (0..1),
        "reason": str,
        "features": { "ma_fast": float, "ma_slow": float, "close": float }
      }

    RULE (baseline)
      - BULL: close > MA_fast*(1+Ts) AND MA_fast > MA_slow AND slope(MA_fast) >= min_ma_slope
      - BEAR: close < MA_slow*(1+Ws)
      - else NEUTRAL

    FAILURE POLICY
      - raise ValueError for insufficient data to compute required MAs
    """
    close = market_df["close"]
    if len(close) < max(params.ma_fast, params.ma_slow):
        raise ValueError("Insufficient bars for regime MAs.")

    ma_f = _sma(close, params.ma_fast)
    ma_s = _sma(close, params.ma_slow)

    c = float(close.iloc[-1])
    mf = float(ma_f.iloc[-1])
    ms = float(ma_s.iloc[-1])

    # slope: last - prev (simple, deterministic)
    mf_prev = float(ma_f.iloc[-2]) if len(ma_f) >= 2 else mf
    slope = mf - mf_prev

    is_bear = c < ms * (1.0 + params.bear_buffer)
    is_bull = (c > mf * (1.0 + params.bull_buffer)) and (mf > ms) and (slope >= params.min_ma_slope)

    if is_bear:
        regime: Regime = "BEAR"
        reason = "close below MA_slow threshold"
    elif is_bull:
        regime = "BULL"
        reason = "close above MA_fast threshold + trend aligned"
    else:
        regime = "NEUTRAL"
        reason = "no bull/bear condition met"

    # confidence: simple deterministic heuristic (0..1)
    # - bull: distance above MA_fast scaled by MA_fast
    # - bear: distance below MA_slow scaled by MA_slow
    # - neutral: small confidence
    if regime == "BULL":
        conf = min(1.0, max(0.0, (c - mf) / max(1e-12, mf)))
    elif regime == "BEAR":
        conf = min(1.0, max(0.0, (ms - c) / max(1e-12, ms)))
    else:
        conf = 0.25

    return {
        "regime": regime,
        "confidence": float(conf),
        "reason": reason,
        "features": {"ma_fast": mf, "ma_slow": ms, "close": c, "ma_fast_slope": float(slope)},
    }
