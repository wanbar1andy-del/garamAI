# garam_core/execution/cost_model.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Side = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class CostModel:
    """
    Conservative cost model (v0.1+):
      - commission: per notional (e.g., 0.00015 = 1.5bp)
      - slippage:   per notional (applied both sides)
      - tax:        applied on SELL notional (Korea stock tax etc; set per your policy)
    """
    commission_rate: float = 0.00015
    slippage_rate: float = 0.00025  # 2.5bp (Locked)
    sell_tax_rate: float = 0.00230  # 0.23% (Locked)

    def cost_rate(self, side: Side) -> float:
        tax = self.sell_tax_rate if side == "SELL" else 0.0
        return self.commission_rate + self.slippage_rate + tax
