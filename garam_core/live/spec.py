# garam_core/live/spec.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LiveSpec:
    symbols: List[str]
    timeframe: str           # "minute"
    bar_interval: int        # 1
    base_equity: float       # 시작 자본 or 기준 자본
    max_leverage: float = 1.0

    # Risk Limits
    max_mdd: float = 0.20            # 계좌 전체 MDD 한도
    max_daily_loss: float = 0.05     # 일 손실 한도 (vs base_equity)
    max_consecutive_loss: int = 5    # 연속 손실 횟수 제한

    # Portfolio Ops
    topk: int = 3
    weight_mode: str = "equal"       # "equal" or "score"

    # Logging
    log_dir: str = "logs/live"
    tag: Optional[str] = None
