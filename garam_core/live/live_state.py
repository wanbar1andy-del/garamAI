# garam_core/live/live_state.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LivePositionState:
    in_position: bool = False
    position_size: float = 0.0
    entry_price: float = 0.0
    multiplier: float = 1.0

    def reset(self):
        self.in_position = False
        self.position_size = 0.0
        self.entry_price = 0.0
        self.multiplier = 1.0
