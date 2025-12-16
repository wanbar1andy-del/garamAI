# garam_core/live/live_runner_stack.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import pandas as pd

from garam_core.live.engine_stack import EngineStack, EngineStackSpec, StackDecision
from garam_core.live.order_router import OrderRouter, Order
from garam_core.live.execution_guard import ExecutionGuardParams, guard_position_size


@dataclass
class LiveStackRunner:
    stack: EngineStack
    router: OrderRouter
    guard: ExecutionGuardParams
    equity: float = 100_000_000.0
    last_fill: Optional[dict] = None  # To expose fill result

    def on_bar(
        self,
        ts: pd.Timestamp,
        ohlcv_window: pd.DataFrame,
        fear_score: float,
        fear_series_window: Optional[pd.Series] = None,
        price_for_fill: Optional[float] = None,
        dry: bool = True,
    ) -> StackDecision:
        # Reset last fill
        self.last_fill = None
        
        d = self.stack.on_bar(ts, ohlcv_window, fear_score, fear_series_window=fear_series_window)

        px = float(price_for_fill) if price_for_fill is not None else float(ohlcv_window["close"].iloc[-1])

        # BUY
        if d.action == "BUY":
            qty = guard_position_size(
                equity=self.equity,
                price=px,
                multiplier=d.multiplier,
                params=self.guard,
            )
            res = self.router.send(Order(side="BUY", qty=qty, price=px, reason=d.reason))
            self.last_fill = res
            if res.get("mode") in ("DRY", "LIVE"):
                # DRY에서도 상태 업데이트(“가동 검증” 목적)
                self.stack.on_fill("BUY", px, qty)

        # PARTIAL SELL
        elif d.action == "PARTIAL_SELL":
            sell_qty = max(0.0, self.stack.state.position_qty * d.qty_frac)
            res = self.router.send(Order(side="SELL", qty=sell_qty, price=px, reason=d.reason))
            self.last_fill = res
            # 상태 업데이트
            self.stack.on_fill("SELL", px, sell_qty)

        # REBUY
        elif d.action == "REBUY":
            add_qty = guard_position_size(
                equity=self.equity,
                price=px,
                multiplier=max(1.0, d.multiplier),
                params=self.guard,
            ) * d.qty_frac
            res = self.router.send(Order(side="BUY", qty=add_qty, price=px, reason=d.reason))
            self.last_fill = res
            self.stack.on_fill("BUY", px, add_qty)

        # FULL SELL
        elif d.action == "SELL":
            res = self.router.send(Order(side="SELL", qty=self.stack.state.position_qty, price=px, reason=d.reason))
            self.last_fill = res
            self.stack.on_fill("SELL", px, self.stack.state.position_qty)

        return d
