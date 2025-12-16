# garam_core/engine/state.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionState:
    in_position: bool = False
    entry_price: Optional[float] = None
    cooldown: int = 0
