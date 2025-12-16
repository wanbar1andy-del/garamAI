# garam_core/engine/signal_profit_first.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd

from garam_core.engine.edge import edge_score


@dataclass(frozen=True)
class ProfitFirstSignalParams:
    momentum_n: int = 60
    base_threshold: float = 0.01      # 기본 1%
    threshold_min: float = 0.003      # 엣지 높으면 0.3%까지 낮춤 (공격)
    threshold_max: float = 0.03       # 엣지 낮으면 3%까지 높임 (쓰레기 트레이드 제거)
    cooldown_bars: int = 0            # 거래 억제 금지(기본 0)
    
    # Compatibility with standard SignalParams for duck typing
    allow_buy_in_neutral: bool = True 
    allow_buy_in_bear: bool = True
    
    # A7 Integration
    use_reversal_filter: bool = False # If True, requires A7 signal (Heat+Pressure) for BUY


def decide_signal_profit_first(
    ohlcv_window: pd.DataFrame,
    params: ProfitFirstSignalParams,
    in_position: bool,
    cooldown_left: int,
) -> Dict[str, Any]:
    c = ohlcv_window["close"]
    n = int(params.momentum_n)
    if len(c) < n + 2:
        return {"action": "HOLD", "reason": "warmup"}

    # 엣지 점수
    e = edge_score(ohlcv_window)

    # 동적 문턱
    # e=0 -> thr=max, e=1 -> thr=min
    thr = params.threshold_max - e * (params.threshold_max - params.threshold_min)
    thr = float(max(params.threshold_min, min(params.threshold_max, thr)))

    # 모멘텀
    # Simple rate of return over N bars
    p_last = float(c.iloc[-1])
    p_prev = float(c.iloc[-1 - n])
    ret_n = (p_last / p_prev) - 1.0

    # 쿨다운은 0이 기본(사용자가 원하면 나중에 “리버스 방지”로만 사용)
    if cooldown_left > 0 and not in_position:
        return {"action": "HOLD", "reason": f"cooldown({cooldown_left})", "edge": e, "thr": thr, "ret_n": ret_n, "cooldown_next": max(0, cooldown_left-1)}

    if not in_position:
        # Check A7 Filter if enabled
        if params.use_reversal_filter:
            from garam_core.engine.alpha_reversal import decide_alpha_a7, AlphaA7Params
            # Use default params for now or extend ProfitFirstSignalParams to hold them?
            # User requirement is specific: Top 30%, Vol Pressure > 0.5.
            # alpha_reversal.py defaults match this (0.7, 0.5).
            a7 = decide_alpha_a7(ohlcv_window, AlphaA7Params())
            if not a7["signal"]:
                return {"action": "HOLD", "reason": "blocked_by_reversal_filter", "edge": e, "thr": thr, "a7": a7}

        if ret_n >= thr:
            return {"action": "BUY", "reason": "edge_momentum_entry", "edge": e, "thr": thr, "ret_n": ret_n, "cooldown_next": 0}
        return {"action": "HOLD", "reason": "no_entry", "edge": e, "thr": thr, "ret_n": ret_n, "cooldown_next": 0}

    # in_position: 기본은 turbo/fast-exit이 관리. 여기서는 HOLD.
    return {"action": "HOLD", "reason": "in_position", "edge": e, "thr": thr, "ret_n": ret_n, "cooldown_next": 0}
