# garam_core/engine/turbo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Literal
import pandas as pd


@dataclass(frozen=True)
class TurboParams:
    """
    Turbo overlay contract:
    - Base exposure is 1.0
    - Turbo adds overlay up to max_multiplier
    - If risk_state OFF -> multiplier must be 1.0
    """
    max_multiplier: float = 2.5
    min_multiplier: float = 1.0

    # volatility targeting (simple, deterministic)
    vol_window: int = 20
    target_vol: float = 0.02      # target std of returns (per bar)
    vol_floor: float = 0.002      # prevent division explosion
    vol_ceiling: float = 0.10

    # fast-exit triggers
    fast_exit_on_bear: bool = True
    fast_exit_drawdown: float = 0.03  # 3% drop from entry triggers exit_fast


def _returns_std(close: pd.Series, n: int) -> float:
    if len(close) < (n + 1):
        raise ValueError("Insufficient bars for volatility.")
    r = close.pct_change().iloc[-n:]  # deterministic enough, but relies on pandas; acceptable for core
    return float(r.std(ddof=0))       # ddof=0 for determinism


def turbo_overlay(
    market_df: pd.DataFrame,
    signal_state: Dict[str, Any],
    regime_state: Dict[str, Any],
    position_state: Dict[str, Any],
    params: TurboParams,
) -> Dict[str, Any]:
    """
    PURPOSE
      Compute leverage overlay (multiplier) and fast-exit recommendation.

    INPUT CONTRACT
      - market_df: Gate1 passed
      - signal_state: output of decide_signal()
      - regime_state: output of classify_regime()
      - position_state:
          {
            "in_position": bool,
            "entry_price": float|None
          }

    OUTPUT CONTRACT
      {
        "multiplier": float,         # [min_multiplier, max_multiplier]
        "risk_state": "ON"|"OFF",
        "exit_fast": bool,
        "reason": str,
        "features": { "vol": float, "target_vol": float, ... }
      }

    RULE (minimal)
      - risk_state ON only when:
          (regime == "BULL") AND (signal_state action in ["BUY","HOLD"] with strength>0)
      - multiplier scales by target_vol / realized_vol (clipped), then clipped to [1.0, max_multiplier]
      - exit_fast true when:
          - fast_exit_on_bear and regime == "BEAR"
          - OR (in_position and entry_price and drawdown >= fast_exit_drawdown)

    FAILURE POLICY
      - raise ValueError if volatility cannot be computed due to insufficient bars
    """
    close = market_df["close"]
    regime = regime_state.get("regime", "NEUTRAL")
    action = signal_state.get("action", "HOLD")
    strength = float(signal_state.get("strength", 0.0))

    in_pos = bool(position_state.get("in_position", False))
    entry_price = position_state.get("entry_price", None)
    last_price = float(close.iloc[-1])

    vol = _returns_std(close, params.vol_window)
    vol = min(params.vol_ceiling, max(params.vol_floor, vol))

    # base overlay: target/realized
    raw_mult = params.target_vol / vol
    mult = min(params.max_multiplier, max(params.min_multiplier, raw_mult))

    risk_on = (regime == "BULL") and (action in ("BUY", "HOLD")) and (strength > 0.0)
    if not risk_on:
        mult = params.min_multiplier  # OFF -> 1.0
        risk_state = "OFF"
        reason = "risk OFF: regime/action/strength not eligible"
    else:
        risk_state = "ON"
        reason = "risk ON: bull regime eligible; vol-target applied"

    # fast exit logic
    exit_fast = False
    if params.fast_exit_on_bear and regime == "BEAR":
        exit_fast = True

    if in_pos and entry_price is not None:
        ep = float(entry_price)
        if ep > 0:
            dd = (ep - last_price) / ep
            if dd >= params.fast_exit_drawdown:
                exit_fast = True

    return {
        "multiplier": float(mult),
        "risk_state": risk_state,
        "exit_fast": bool(exit_fast),
        "reason": reason,
        "features": {
            "vol": float(vol),
            "target_vol": float(params.target_vol),
            "raw_multiplier": float(raw_mult),
            "regime": regime,
            "action": action,
            "strength": float(strength),
            "last_price": float(last_price),
            "entry_price": float(entry_price) if entry_price is not None else None,
        },
    }
