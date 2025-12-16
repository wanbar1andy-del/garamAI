# garam_core/execution/fill_model.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional
import pandas as pd


Side = Literal["BUY", "SELL"]
FillMethod = Literal["NEXT_OPEN", "NEXT_CLOSE", "NEXT_VWAP_PROXY"]


@dataclass(frozen=True)
class FillSpec:
    """
    Deterministic fill model.
    - NEXT_OPEN: fill at next bar open
    - NEXT_CLOSE: fill at next bar close
    - NEXT_VWAP_PROXY: (open+high+low+close)/4 of next bar
    """
    method: FillMethod = "NEXT_OPEN"


def get_fill_price(next_bar: pd.Series, spec: FillSpec, side: Side) -> float:
    """
    next_bar: Series with open/high/low/close (validated by schema gate upstream)
    side: included for future extensions (e.g., asymmetric slippage); not used in v0.1
    """
    if spec.method == "NEXT_OPEN":
        return float(next_bar["open"])
    if spec.method == "NEXT_CLOSE":
        return float(next_bar["close"])
    if spec.method == "NEXT_VWAP_PROXY":
        return float((next_bar["open"] + next_bar["high"] + next_bar["low"] + next_bar["close"]) / 4.0)
    raise ValueError(f"Unknown fill method: {spec.method}")
