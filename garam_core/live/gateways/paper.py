# garam_core/live/gateways/paper.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any

from garam_core.live.interfaces import ExecutionGateway

@dataclass
class PaperGateway(ExecutionGateway):
    cash: float
    positions: Dict[str, float] = field(default_factory=dict)

    def send_order(self, symbol: str, side: str, qty: int, price: float | None = None) -> Any:
        if qty <= 0:
            return None
        if price is None:
            raise ValueError("PaperGateway requires price (simulated market order)")

        sign = 1 if side == "BUY" else -1
        cost = qty * price * sign
        
        # Simple execution: Fill immediately
        self.cash -= cost
        self.positions[symbol] = self.positions.get(symbol, 0.0) + (qty * sign)
        
        # Clean up zero positions
        if abs(self.positions[symbol]) < 1e-9:
             del self.positions[symbol]

        return {"symbol": symbol, "side": side, "qty": qty, "price": price, "status": "FILLED"}

    def get_positions(self) -> Dict[str, float]:
        return dict(self.positions)

    def get_cash(self) -> float:
        return self.cash
