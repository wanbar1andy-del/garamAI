# garam_core/engine/position_manager.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class PositionManagerParams:
    # 부분익절 트리거(진입가 대비)
    tp1: float = 0.006          # +0.6%
    tp2: float = 0.012          # +1.2%

    # 부분익절 비중
    tp1_frac: float = 0.35
    tp2_frac: float = 0.35
    # 나머지 0.30은 러너로 유지

    # 재진입 조건
    reentry_pullback: float = 0.004   # 고점 대비 -0.4% 조정 시 재진입 후보
    reentry_max: int = 2              # 러너 재장전 횟수 제한(과열 방지용)

    # 러너 트레일 (수익 확대)
    trail_from_peak: float = 0.006    # 고점 대비 -0.6%면 러너 정리


@dataclass
class PositionManagerState:
    peak_price: float = 0.0
    tp1_done: bool = False
    tp2_done: bool = False
    reentry_count: int = 0


def init_pm_state(entry_price: float) -> PositionManagerState:
    return PositionManagerState(peak_price=float(entry_price))


def update_position_manager(
    entry_price: float,
    last_price: float,
    pos_qty: float,
    pm_state: PositionManagerState,
    p: PositionManagerParams,
) -> Dict[str, Any]:
    """
    Returns:
      action: HOLD / PARTIAL_SELL / FULL_SELL / REBUY
      qty_frac: 비율(0~1) - PARTIAL_SELL/REBUY에 사용
      reason
      state: updated state
    """
    ep = float(entry_price)
    px = float(last_price)

    # peak update
    pm_state.peak_price = max(pm_state.peak_price, px)

    pnl = (px / ep) - 1.0 if ep > 0 else 0.0
    dd_from_peak = (px / pm_state.peak_price) - 1.0 if pm_state.peak_price > 0 else 0.0 # negative

    # 1) 부분익절 1
    if (not pm_state.tp1_done) and (pnl >= p.tp1):
        pm_state.tp1_done = True
        return {
            "action": "PARTIAL_SELL",
            "qty_frac": float(p.tp1_frac),
            "reason": "take_profit_1",
            "pnl": pnl,
            "dd_from_peak": dd_from_peak,
            "state": pm_state,
        }

    # 2) 부분익절 2
    if (not pm_state.tp2_done) and (pnl >= p.tp2):
        pm_state.tp2_done = True
        return {
            "action": "PARTIAL_SELL",
            "qty_frac": float(p.tp2_frac),
            "reason": "take_profit_2",
            "pnl": pnl,
            "dd_from_peak": dd_from_peak,
            "state": pm_state,
        }

    # 3) 러너 트레일: 고점 대비 조정이 일정 이상이면 러너 정리
    if dd_from_peak <= -abs(p.trail_from_peak):
        return {
            "action": "FULL_SELL",
            "qty_frac": 1.0,
            "reason": "runner_trail_exit",
            "pnl": pnl,
            "dd_from_peak": dd_from_peak,
            "state": pm_state,
        }

    # 4) 재진입(재장전): 고점 대비 조정 후, 다시 먹을 기회
    # - 포지션이 남아 있어야 의미 있음(러너 유지 상태)
    if pm_state.reentry_count < p.reentry_max:
        pullback = (px / pm_state.peak_price) - 1.0
        if pullback <= -abs(p.reentry_pullback):
            pm_state.reentry_count += 1
            return {
                "action": "REBUY",
                "qty_frac": float(min(0.35, 1.0)),  # 기본 재장전 비중(1.0 means 100% of sizing usually, here likely frac relative to logic)
                # User prompted min(0.35, 1.0) basically hardcoded 0.35
                "reason": "reentry_reload",
                "pnl": pnl,
                "dd_from_peak": dd_from_peak,
                "state": pm_state,
            }

    return {
        "action": "HOLD",
        "qty_frac": 0.0,
        "reason": "hold",
        "pnl": pnl,
        "dd_from_peak": dd_from_peak,
        "state": pm_state,
    }
