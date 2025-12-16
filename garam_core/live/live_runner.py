# garam_core/live/live_runner.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional
import pandas as pd

from garam_core.engine.regime import classify_regime, RegimeParams
from garam_core.engine.signal import decide_signal, SignalParams
from garam_core.engine.turbo import turbo_overlay, TurboParams
from garam_core.risk.fear_gate import eval_fear_gate, FearGateParams
from garam_core.live.live_state import LivePositionState


@dataclass
class LiveDecision:
    ts: pd.Timestamp
    action: str                # BUY / SELL / HOLD / BLOCKED
    reason: str
    multiplier: float
    fear_score: float
    regime: str
    debug: Dict[str, Any]


class LiveRunner:
    def __init__(
        self,
        signal_params: SignalParams,
        turbo_params: TurboParams,
        regime_params: RegimeParams,
        fear_gate: FearGateParams,
    ):
        self.signal_params = signal_params
        self.turbo_params = turbo_params
        self.regime_params = regime_params
        self.fear_gate = fear_gate

        self.state = LivePositionState()

    def on_bar(
        self,
        ts: pd.Timestamp,
        ohlcv_window: pd.DataFrame,   # 최근 N bars (분봉)
        fear_score: float,
    ) -> LiveDecision:

        # 1) Regime
        regime_state = classify_regime(ohlcv_window, self.regime_params)
        regime = regime_state["regime"]

        # 2) Signal
        sig = decide_signal(
            market_df=ohlcv_window,
            params=self.signal_params,
            regime_state=regime_state,
            position_state={
                "in_position": self.state.in_position,
                "cooldown": getattr(self.state, "cooldown", 0), 
                "entry_price": self.state.entry_price,
            },
        )

        action = sig["action"]
        # reason not always in sig, but let's check
        reason = sig.get("reason", action)
        
        # update state cooldown if we want to be correct next bar (DRY-RUN simulation)
        self.state.cooldown = int(sig["cooldown_next"])

        # 3) Turbo
        turbo = turbo_overlay(
            market_df=ohlcv_window,
            signal_state=sig,
            regime_state=regime_state,
            position_state={
                "in_position": self.state.in_position,
                "entry_price": self.state.entry_price,
            },
            params=self.turbo_params,
        )
        multiplier = float(turbo.get("multiplier", 1.0))
        exit_fast = bool(turbo.get("exit_fast", False))

        # 4) Fear Gate
        fg = eval_fear_gate(fear_score, self.fear_gate)

        # Logic mapping
        final_action = action
        final_reason = reason
        
        # Priority: Exit > Block > Entry
        if self.state.in_position:
             if action == "SELL":
                 final_action = "SELL"
                 final_reason = "Signal Exit"
             elif exit_fast:
                 final_action = "SELL"
                 final_reason = "Turbo Fast Exit"
        else:
             # Not in position
             if action == "BUY":
                 # Check Block
                 if not fg["entry_allowed"]:
                     final_action = "BLOCKED"
                     final_reason = f"FearGate:{fg['reason']}"
                 else:
                     # Cap multiplier
                     capped = min(multiplier, fg["multiplier_cap"])
                     multiplier = capped
             else:
                 final_action = "HOLD"

        # 5) State update (DRY-RUN: 상태만 변경 - but on_bar implies mutation or just decision?)
        # The user's code showed mutation inside on_bar.
        if final_action == "BUY" and not self.state.in_position:
            self.state.in_position = True
            self.state.multiplier = multiplier
            # self.state.entry_price needed? Yes, typically close of this bar (fill next)
            # In live runner bar-by-bar, we are at 'ts'. Fill assumed?
            # Replay fills next bar. Live sends order now.
            # Let's assume fill at current close for state tracking purposes.
            self.state.entry_price = float(ohlcv_window["close"].iloc[-1])
            
        elif final_action == "SELL" and self.state.in_position:
            self.state.reset()

        return LiveDecision(
            ts=ts,
            action=final_action,
            reason=final_reason,
            multiplier=multiplier,
            fear_score=fear_score,
            regime=str(regime),
            debug={"signal": sig, "turbo": turbo},
        )
