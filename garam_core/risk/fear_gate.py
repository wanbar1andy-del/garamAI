# garam_core/risk/fear_gate.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class FearGateParams:
    enabled: bool = True
    block_entry_above: float = 0.85   # fear_score가 이 값보다 크면 신규 진입 차단
    multiplier_cap: float = 1.3       # fear 구간에서 multiplier 상한


def eval_fear_gate(fear_score: float, p: FearGateParams) -> Dict[str, Any]:
    """
    Returns:
      entry_allowed: bool
      multiplier_cap: float
      reason: str
    """
    if not p.enabled:
        return {"entry_allowed": True, "multiplier_cap": 10.0, "reason": "fear_gate_disabled"}

    fs = float(fear_score)
    if fs >= p.block_entry_above:
        return {"entry_allowed": False, "multiplier_cap": float(p.multiplier_cap), "reason": "fear_block_entry"}
    return {"entry_allowed": True, "multiplier_cap": float(p.multiplier_cap), "reason": "fear_cap_only"}
