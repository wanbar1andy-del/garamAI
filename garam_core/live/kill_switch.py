# garam_core/live/kill_switch.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class KillSwitchParams:
    enabled: bool = True
    max_total_loss: float = 0.20         # -20% 누적 손실 한계선
    hard_stop: bool = True               # 한계 도달 시 즉시 중단


@dataclass
class KillSwitchState:
    peak_equity: float = 0.0
    equity: float = 0.0
    halted: bool = False

    def update(self, equity: float):
        self.equity = float(equity)
        if self.peak_equity <= 0:
            self.peak_equity = float(equity)
        self.peak_equity = max(self.peak_equity, float(equity))

    @property
    def drawdown(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return (self.equity / self.peak_equity) - 1.0  # negative


def eval_kill_switch(state: KillSwitchState, params: KillSwitchParams) -> Dict[str, Any]:
    """
    Evaluates if trading should be halted based on relaxed Profit-First rules.
    Only halts on deep drawdown (max_total_loss).
    """
    if not params.enabled:
        return {"allowed": True, "reason": "disabled"}

    if state.halted:
        return {"allowed": False, "reason": "already_halted"}

    dd = -state.drawdown  # drawdown magnitude (positive)
    if dd >= params.max_total_loss:
        if params.hard_stop:
            state.halted = True
        return {"allowed": False, "reason": f"max_total_loss({params.max_total_loss:.2f})"}

    return {"allowed": True, "reason": "ok"}
