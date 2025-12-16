# garam_core/live/state.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
import pandas as pd

@dataclass
class LiveAccountState:
    equity: float
    peak_equity: float
    daily_pnl: float = 0.0
    consecutive_losses: int = 0

    positions: Dict[str, float] = field(default_factory=dict)   # {symbol: qty}
    last_price: Dict[str, float] = field(default_factory=dict)  # {symbol: last_close}

    def update_mark_to_market(self, prices: Dict[str, float], cash_balance: float = 0.0) -> None:
        self.last_price.update(prices)
        pos_value = sum(qty * self.last_price.get(sym, 0.0) for sym, qty in self.positions.items())
        # Equity = Cash + Position Value
        self.equity = cash_balance + pos_value
        
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity

    @property
    def mdd(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return (self.equity - self.peak_equity) / self.peak_equity

    def register_trade_result(self, pnl: float):
        self.daily_pnl += pnl
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
