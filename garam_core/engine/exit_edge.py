# garam_core/engine/exit_edge.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd

from garam_core.engine.edge import edge_score


@dataclass(frozen=True)
class EdgeExitParams:
    edge_exit_th: float = 0.25
    confirm_bars: int = 3


def update_edge_exit_streak(
    ohlcv_window: pd.DataFrame,
    streak: int,
    p: EdgeExitParams,
) -> Dict[str, Any]:
    e = edge_score(ohlcv_window)
    if e < p.edge_exit_th:
        streak2 = streak + 1
    else:
        streak2 = 0

    should_exit = (streak2 >= p.confirm_bars)
    return {
        "edge": float(e),
        "streak": int(streak2),
        "should_exit": bool(should_exit),
        "reason": "edge_decay_exit" if should_exit else "hold",
    }
