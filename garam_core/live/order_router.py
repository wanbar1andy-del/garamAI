# garam_core/live/order_router.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import csv

from garam_core.execution.cost_model import CostModel


@dataclass(frozen=True)
class Order:
    side: str           # "BUY" or "SELL"
    qty: float
    price: float
    reason: str = ""


class OrderRouter:
    """
    - CostModel 주입 필수
    - cash_delta:
        BUY  -> -(notional + cost)
        SELL -> +(notional - cost)
    """
    def __init__(
        self,
        *,
        mode: str = "DRY",
        cost_model: Optional[CostModel] = None,
        cost_log_path: Optional[Path] = None,
    ):
        self.mode = mode
        self.cost_model = cost_model or CostModel(
            commission_rate=0.00015,
            slippage_rate=0.00025,
            sell_tax_rate=0.00230,
        )
        self.last_fill: Optional[Dict[str, Any]] = None

        # 포지션 추적(최소)
        self.position_qty: float = 0.0
        self.avg_price: float = 0.0

        # 비용 로그
        self.cost_log_path = cost_log_path
        if self.cost_log_path:
            self.cost_log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.cost_log_path.exists():
                with self.cost_log_path.open("w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([
                        "side","qty","price","notional",
                        "commission","slippage","tax","total_cost"
                    ])

    def _calc_cost(self, side: str, notional: float) -> Dict[str, float]:
        c = self.cost_model
        commission = notional * c.commission_rate
        slippage   = notional * c.slippage_rate
        tax        = notional * c.sell_tax_rate if side == "SELL" else 0.0
        total = commission + slippage + tax
        return {
            "commission": float(commission),
            "slippage": float(slippage),
            "tax": float(tax),
            "total": float(total),
        }

    def _log_cost(self, side, qty, price, notional, cost):
        if not self.cost_log_path:
            return
        with self.cost_log_path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                side, qty, price, notional,
                cost["commission"], cost["slippage"], cost["tax"], cost["total"]
            ])

    def send(self, order: Order) -> Dict[str, Any]:
        side = order.side.upper()
        qty = float(order.qty)
        px = float(order.price)
        notional = qty * px

        cost = self._calc_cost(side, notional)

        if side == "BUY":
            cash_delta = -(notional + cost["total"])
            # 포지션 업데이트
            if self.position_qty <= 0:
                self.position_qty = qty
                self.avg_price = px
            else:
                new_notional = self.position_qty * self.avg_price + notional
                self.position_qty += qty
                self.avg_price = new_notional / max(1e-12, self.position_qty)

        elif side == "SELL":
            if qty <= 0:
                qty = self.position_qty
                notional = qty * px
                cost = self._calc_cost(side, notional)
            cash_delta = +(notional - cost["total"])
            self.position_qty = max(0.0, self.position_qty - qty)
            if self.position_qty == 0:
                self.avg_price = 0.0
        else:
            raise ValueError(f"Unknown side: {side}")

        self._log_cost(side, qty, px, notional, cost)

        fill = {
            "mode": self.mode,
            "filled": True,
            "side": side,
            "qty": qty,
            "price": px,
            "notional": notional,
            "cost": cost,
            "cash_delta": float(cash_delta),
            "reason": order.reason,
        }
        self.last_fill = fill
        return fill

    def send_buy(self, price: float, qty: float, reason: str = "") -> Dict[str, Any]:
        return self.send(Order(side="BUY", qty=qty, price=price, reason=reason))

    def send_sell(self, price: float, qty: float, reason: str = "") -> Dict[str, Any]:
        return self.send(Order(side="SELL", qty=qty, price=price, reason=reason))
