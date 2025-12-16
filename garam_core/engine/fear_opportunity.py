# garam_core/engine/fear_opportunity.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd
import numpy as np


@dataclass(frozen=True)
class FearOpportunityParams:
    # 공포 급등 조건
    fear_spike: float = 0.90           # fear_score >= 0.90
    fear_rise_min: float = 0.15        # 최근 window 대비 최소 상승폭
    fear_window: int = 60              # 60분 기준

    # 가격 조건(패닉 후 반전)
    drop_min: float = -0.008           # 최근 N분 대비 -0.8% 이상 급락
    rebound_confirm: float = 0.003     # 직전 10분 +0.3% 반등 확인
    price_window: int = 60

    # 신호 세기(추가 레버리지/추가 진입 비율에 활용 가능)
    bonus_mult: float = 0.25           # “기회 신호” 시 multiplier에 +0.25 (캡 적용)


def fear_opportunity_signal(
    ohlcv_window: pd.DataFrame,
    fear_window_series: pd.Series,     # market-aligned fear_score 시계열(ohlcv_window.index 포함)
    p: FearOpportunityParams,
) -> Dict[str, Any]:
    """
    Returns:
      trigger: bool
      reason
      bonus_mult
      score
    """
    # Need sufficient history
    if len(ohlcv_window) < max(p.fear_window, p.price_window) + 5:
        return {"trigger": False, "reason": "warmup", "bonus_mult": 0.0, "score": 0.0}

    # Align check: ensure fear_window_series covers needed index
    # We use reindex/ffill to be safe
    try:
        fear = fear_window_series.reindex(ohlcv_window.index).ffill()
    except Exception:
        return {"trigger": False, "reason": "fear_data_error", "bonus_mult": 0.0, "score": 0.0}
        
    fs_now = float(fear.iloc[-1])

    if len(fear) <= p.fear_window:
         return {"trigger": False, "reason": "insufficient_fear_history", "bonus_mult": 0.0, "score": 0.0}

    fear_ref = float(fear.iloc[-1 - p.fear_window])
    fear_rise = fs_now - fear_ref

    c = ohlcv_window["close"]
    px_now = float(c.iloc[-1])
    px_ref = float(c.iloc[-1 - p.price_window])
    drop = (px_now / px_ref) - 1.0

    # rebound confirm (최근 10분 반등)
    px_10 = float(c.iloc[-11]) if len(c) >= 11 else float(c.iloc[0])
    rebound = (px_now / px_10) - 1.0

    cond = (
        (fs_now >= p.fear_spike) and
        (fear_rise >= p.fear_rise_min) and
        (drop <= p.drop_min) and
        (rebound >= p.rebound_confirm)
    )

    if not cond:
        return {
            "trigger": False,
            "reason": "no_fear_opportunity",
            "bonus_mult": 0.0,
            "score": float(np.clip(fs_now, 0, 1)),
        }

    # score: 공포+반등 강도 결합
    score = float(np.clip(0.6 * fs_now + 0.4 * min(1.0, rebound / max(1e-9, p.rebound_confirm)), 0, 1))
    return {
        "trigger": True,
        "reason": "fear_spike_reversal_opportunity",
        "bonus_mult": float(p.bonus_mult),
        "score": score,
    }
