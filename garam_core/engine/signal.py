# garam_core/engine/signal.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any
import pandas as pd


Action = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class SignalParams:
    """
    Contract Notes
    - cooldown_bars: number of bars to block new BUY after an exit.
    - momentum_n: bars for momentum confirmation.
    - min_momentum: minimum momentum (fraction) to allow BUY.
    
    [Vol-Scaled Extensions]
    - use_vol_scaled_momentum: if True, min_momentum is ignored, uses k * vol
    - vol_lookback: n bars for volatility calculation (std of returns)
    - min_momentum_k: multiplier for vol-scaled threshold
    - abs_momentum_floor: minimum absolute threshold (noise filter)
    - use_vol_scaled_cooldown: if True, cooldown_bars is base, scaled by vol/target
    - cooldown_target_vol: reference volatility for cooldown scaling
    """
    cooldown_bars: int = 10
    momentum_n: int = 5
    min_momentum: float = 0.00

    # regime gating
    allow_buy_in_neutral: bool = False
    allow_buy_in_bear: bool = False

    # vol-scaled logic
    use_vol_scaled_momentum: bool = True
    vol_lookback: int = 20           
    min_momentum_k: float = 1.0
    # PROVISIONAL: 0.2% validated for Low Vol (Samsung), but likely too high for High Vol (Hynix).
    # Pending Bucket-Adaptive Tuning (Phase 16).
    abs_momentum_floor: float = 0.002
    cost_floor: float = 0.0025      # [NEW] Cost-based floor (0.25% covers fee+slip)
    
    use_vol_scaled_cooldown: bool = False
    cooldown_target_vol: float = 0.01
    cooldown_min: int = 30
    cooldown_max: int = 360


def _momentum(close: pd.Series, n: int) -> float:
    # deterministic, no pct_change dependency quirks:
    # (last / nth_previous) - 1
    if len(close) <= n:
        raise ValueError("Insufficient bars for momentum.")
    prev = float(close.iloc[-(n + 1)])
    last = float(close.iloc[-1])
    return (last / max(1e-12, prev)) - 1.0

def _volatility(close: pd.Series, n: int) -> float:
    if len(close) <= n + 1:
        return 0.001 # Default fallback
    # Optimization: Slice strictly needed tail (n+1 needed for n returns)
    subset = close.iloc[-(n + 2):] 
    rets = subset.pct_change().tail(n)
    return float(rets.std())

def decide_signal(
    ohlcv_window: pd.DataFrame,
    regime_state: Dict[str, Any],
    params: SignalParams,
    position_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Decide BUY/SELL/HOLD signal based on Vol-Scaled Momentum.
    LOGIC FROZEN: Phase 15 (Restoration).

    PURPOSE
      Decide BUY/SELL/HOLD (no sizing, no leverage). Uses current regime and basic momentum.

    INPUT CONTRACT
      - market_df: Gate1 passed
      - regime_state: output of classify_regime()
      - position_state:
          {
            "in_position": bool,
            "cooldown": int,         # remaining bars
            "entry_price": float|None
          }
        NOTE: position_state is passed in, not stored globally. Core remains stateless.

    OUTPUT CONTRACT
      {
        "action": "BUY"|"SELL"|"HOLD",
        "strength": float (0..1),
        "cooldown_next": int,      # next remaining cooldown after this bar
        "reason": str,
        "features": { ... }
      }

    BASE RULES (minimal, deterministic)
      - If cooldown > 0: cannot BUY.
      - BUY:
          allowed if NOT in_position AND cooldown==0 AND regime allows buy AND momentum>=min_momentum
      - SELL:
          allowed if in_position AND (regime == "BEAR")  [minimal safety exit]
      - else HOLD

    FAILURE POLICY
      - raise ValueError for insufficient data to compute momentum.
    """
    close_series = ohlcv_window["close"]
    in_pos = bool(position_state.get("in_position", False))
    cooldown = int(position_state.get("cooldown", 0))
    entry_price = position_state.get("entry_price", None)

    # cooldown tick down (deterministic)
    cooldown_next = max(0, cooldown - 1)

    # Feature extraction
    # Ensure sufficient data (Lookback + 2 safety)
    if len(close_series) < max(params.vol_lookback, params.momentum_n) + 2:
        return {
            "action": "HOLD", 
            "strength": 0.0, 
            "cooldown_next": cooldown_next,
            "features": {}, 
            "reason": "INSUFFICIENT_DATA"
        }

    # Consistent Helper Usage
    mom = _momentum(close_series, params.momentum_n)
    vol = _volatility(close_series, params.vol_lookback)

    regime = regime_state.get("regime", "UNKNOWN")
    conf = float(regime_state.get("confidence", 0.5))

    zscore = (mom / vol) if (vol > 1e-12) else 0.0

    # Dynamic Threshold Logic
    if params.use_vol_scaled_momentum:
        thresh_raw = params.min_momentum_k * vol
        thresh_final = max(thresh_raw, params.abs_momentum_floor, params.cost_floor)
    else:
        thresh_raw = params.min_momentum
        thresh_final = max(thresh_raw, params.cost_floor)

    mom_ok = (mom >= thresh_final)
    
    # Floor Hit Detection
    floor_hit = False
    if params.use_vol_scaled_momentum:
        if thresh_final > (thresh_raw + 1e-12):
            floor_hit = True

    # Cooldown Calculation (Internal)
    def calc_cooldown() -> int:
        if params.use_vol_scaled_cooldown and vol > 1e-9:
             ratio = vol / max(1e-9, params.cooldown_target_vol)
             val = params.cooldown_bars * ratio
             return int(max(params.cooldown_min, min(params.cooldown_max, val)))
        return params.cooldown_bars
    
    cooldown_calc_val = calc_cooldown()

    features_dict = {
        "mom_20": float(mom),
        "vol_20": float(vol),
        "regime": regime,
        "thresh_raw": float(thresh_raw),
        "thresh_final": float(thresh_final),
        "zscore": float(zscore),
        "floor_hit": bool(floor_hit),
        "cooldown_calc": int(cooldown_calc_val),
        "regime_conf": conf
    }
    
    # Decision Logic
    allow_buy = (
        (regime == "BULL")
        or (params.allow_buy_in_neutral and regime == "NEUTRAL")
        or (params.allow_buy_in_bear and regime == "BEAR")
    )

    if in_pos:
        # Exit on BEAR regime strict rule
        if regime == "BEAR":
            return {
                "action": "SELL",
                "strength": 1.0,
                # On Exit, we might want to start cooldown? 
                # Original logic: "cooldown_next": cd_val (calc)
                "cooldown_next": cooldown_calc_val,
                "reason": "exit on BEAR regime",
                "features": {**features_dict, "entry_price": entry_price},
            }
        
        # Default Hold
        return {
            "action": "HOLD",
            "strength": 0.5,
            "cooldown_next": cooldown_next, # decrement
            "reason": "in position; no exit trigger",
            "features": {**features_dict, "entry_price": entry_price},
        }

    if cooldown > 0:
        return {
            "action": "HOLD", 
            "strength": 0.2,
            "cooldown_next": cooldown_next,
            "reason": "cooldown active",
            "features": features_dict
        }

    if allow_buy and mom_ok:
        # Scaling Strength based on Confidence and Momentum
        # strength = 0.5 * conf + 0.5 * min(1.0, mom*10)
        strength = min(1.0, max(0.0, 0.5 * conf + 0.5 * min(1.0, max(0.0, mom * 10.0))))
        
        return {
            "action": "BUY",
            "strength": float(strength),
            "cooldown_next": 0, # Consumption happens on exit usually.
            # Wait, if we return 0 here, cooldown doesn't start?
            # Correct. Cooldown starts AFTER trade.
            # But earlier logic had "cooldown_next": cd_val?
            # User snippet: "cooldown_next": 0
            # Let's trust user snippet.
            "features": features_dict,
            "reason": "buy allowed by regime and momentum"
        }
            
    return {
        "action": "HOLD",
        "strength": 0.1,
        "cooldown_next": 0, # Reset if no signal? Or keep 0?
        "features": features_dict,
        "reason": "buy conditions not met"
    }
