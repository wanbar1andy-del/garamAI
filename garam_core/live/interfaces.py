# garam_core/live/interfaces.py
from __future__ import annotations
from typing import Protocol, List, Dict, Any
import pandas as pd

class DataFeed(Protocol):
    """
    Subscribes to symbols and provides next bar data.
    """
    def subscribe(self, symbols: List[str]) -> None:
        ...

    def get_next_bar(self) -> Dict[str, pd.Series]:
        """
        Returns a dict of {symbol: bar_series} for the latest completed bar.
        Returns empty dict if no data available/timeout.
        """
        ...


class ExecutionGateway(Protocol):
    """
    Abstracts order execution and position retrieval.
    """
    def send_order(self, symbol: str, side: str, qty: int, price: float | None = None) -> Any:
        # side: "BUY" / "SELL"
        ...

    def get_positions(self) -> Dict[str, float]:
        # {symbol: qty}
        ...

    def get_cash(self) -> float:
        ...


class PortfolioStore(Protocol):
    """
    Records system state and events.
    """
    def record_bar(self, ts, equity: float, positions: Dict[str, float], meta: Dict[str, Any]) -> None:
        ...

    def record_trade(self, ts, symbol: str, side: str, qty: int, price: float, meta: Dict[str, Any]) -> None:
        ...
