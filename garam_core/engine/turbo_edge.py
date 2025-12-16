# garam_core/engine/turbo_edge.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
import pandas as pd

from garam_core.engine.edge import edge_score


@dataclass(frozen=True)
class EdgeTurboParams:
    base_mult: float = 1.0
    max_mult: float = 2.5

    # 엣지 점수에 따른 레버리지 맵
    # e<=e0: base, e>=e1: max
    e0: float = 0.35
    e1: float = 0.80

    # 변동성 타겟 (기존 Turbo V3 철학 유지)
    target_vol: float = 0.02
    rv_window: int = 60

    # 엣지 기반 fast-exit 조건
    edge_exit_th: float = 0.25        # 엣지가 이 값 아래로 붕괴하면 exit 고려
    edge_exit_confirm: int = 3        # 연속 N바 붕괴 시 확정


def _realized_vol(close: pd.Series, n: int) -> float:
    r = close.pct_change()
    rv = r.rolling(n).std()
    v = float(rv.iloc[-1]) if len(rv) else 0.0
    return max(v, 1e-9)


def _map_edge_to_mult(e: float, p: EdgeTurboParams) -> float:
    # piecewise linear
    if e <= p.e0:
        return p.base_mult
    if e >= p.e1:
        return p.max_mult
    t = (e - p.e0) / (p.e1 - p.e0)
    return p.base_mult + t * (p.max_mult - p.base_mult)


def compute_edge_turbo(
    ohlcv_window: pd.DataFrame,
    params: EdgeTurboParams,
    in_position: bool,
    edge_exit_streak: int,
) -> Dict[str, Any]:
    c = ohlcv_window["close"]

    e = edge_score(ohlcv_window)
    rv = _realized_vol(c, params.rv_window)

    # Vol targeting: target_vol / rv (클램프)
    vol_adj = float(np.clip(params.target_vol / rv, 0.5, 2.0))

    base = _map_edge_to_mult(e, params)
    mult = float(np.clip(base * vol_adj, params.base_mult, params.max_mult))

    # edge-exit streak update is done outside; here we only compute suggestion
    exit_suggest = False
    if in_position and (e < params.edge_exit_th) and (edge_exit_streak + 1 >= params.edge_exit_confirm):
        exit_suggest = True

    return {
        "edge": float(e),
        "rv": float(rv),
        "vol_adj": float(vol_adj),
        "multiplier": float(mult),
        "exit_fast": bool(exit_suggest),  # Map to standard turbo key 'exit_fast'
        "edge_exit_suggest": bool(exit_suggest),
    }
