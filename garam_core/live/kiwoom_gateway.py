# garam_core/live/kiwoom_gateway.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from garam_core.live.interfaces import ExecutionGateway

@dataclass
class KiwoomGateway(ExecutionGateway):
    _kiwoom: Any = None  # Injected KiwoomWrapper
    _positions: Dict[str, float] = field(default_factory=dict)
    _cash: float = 0.0

    def send_order(self, symbol: str, side: str, qty: int, price: float | None = None) -> Any:
        if not self._kiwoom:
            return {"error": "No connection"}
        if qty <= 0:
            return None

        # 1:Buy, 2:Sell
        order_type = 1 if side == "BUY" else 2
        # 00:Limit, 03:Market
        hoga = "00" if price else "03"
        p_val = int(price) if price else 0

        # Sync Order
        ret = self._kiwoom.send_order_wrapper(
            "LIVE_ORDER", "0123", order_type, symbol, qty, p_val, hoga, ""
        )
        return {"status_code": ret, "symbol": symbol, "side": side, "qty": qty}

    def get_positions(self) -> Dict[str, float]:
        return dict(self._positions)

    def get_cash(self) -> float:
        return self._cash

    def _on_position_update(self, symbol: str, qty: float):
        self._positions[symbol] = qty

    def _on_cash_update(self, cash: float):
        self._cash = cash
