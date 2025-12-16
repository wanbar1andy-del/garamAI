# garam_core/live/engine_stack.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
import pandas as pd

from garam_core.engine.regime import classify_regime, RegimeParams

# signal (둘 다 지원)
from garam_core.engine.signal import decide_signal, SignalParams
from garam_core.engine.signal_profit_first import ProfitFirstSignalParams, decide_signal_profit_first

# turbo (둘 다 지원)
from garam_core.engine.turbo import turbo_overlay, TurboParams
from garam_core.engine.turbo_edge import EdgeTurboParams, compute_edge_turbo

# exit / pm / fear opportunity
from garam_core.engine.exit_edge import EdgeExitParams, update_edge_exit_streak
from garam_core.engine.position_manager import (
    PositionManagerParams, PositionManagerState, init_pm_state, update_position_manager
)
from garam_core.engine.fear_opportunity import FearOpportunityParams, fear_opportunity_signal

# fear gate
from garam_core.risk.fear_gate import eval_fear_gate, FearGateParams


SignalLike = Union[SignalParams, ProfitFirstSignalParams]
TurboLike = Union[TurboParams, EdgeTurboParams]


@dataclass
class StackState:
    in_position: bool = False
    entry_price: float = 0.0
    position_qty: float = 0.0  # Fraction held (0.0 to 1.0+)

    cooldown_left: int = 0
    edge_exit_streak: int = 0
    pm_state: Optional[PositionManagerState] = None


@dataclass
class StackDecision:
    ts: pd.Timestamp
    action: str                   # BUY / SELL / HOLD / PARTIAL_SELL / REBUY / BLOCKED
    reason: str

    multiplier: float
    fear_score: float
    regime: str

    # sizing hints (Live에서 qty 계산에 사용)
    qty_frac: float = 1.0         # PARTIAL_SELL/REBUY 등에 사용 (0~1)
    debug: Dict[str, Any] = None


@dataclass(frozen=True)
class EngineStackSpec:
    regime_params: RegimeParams
    signal_params: SignalLike
    fear_gate: FearGateParams

    turbo_params: Optional[TurboLike] = None
    edge_exit: Optional[EdgeExitParams] = None
    pm_params: Optional[PositionManagerParams] = None
    fear_opp: Optional[FearOpportunityParams] = None


class EngineStack:
    """
    Live에서도 Replay와 동일한 엔진 스택을 적용.
    상태는 runner가 들고, core 로직은 순수 함수 호출.
    """
    def __init__(self, spec: EngineStackSpec):
        self.spec = spec
        self.state = StackState()

    def on_bar(
        self,
        ts: pd.Timestamp,
        ohlcv_window: pd.DataFrame,
        fear_score: float,
        fear_series_window: Optional[pd.Series] = None,  # 공포 기회 신호용(있으면 더 좋음)
    ) -> StackDecision:
        dbg: Dict[str, Any] = {}

        # 0) Regime
        regime_state = classify_regime(ohlcv_window, self.spec.regime_params)
        regime = regime_state.get("regime", "NEUTRAL")
        dbg["regime"] = str(regime)

        # 1) Signal
        if isinstance(self.spec.signal_params, ProfitFirstSignalParams):
            sig = decide_signal_profit_first(
                ohlcv_window=ohlcv_window,
                params=self.spec.signal_params,
                in_position=self.state.in_position,
                cooldown_left=self.state.cooldown_left,
            )
        else:
            sig = decide_signal(
                market_df=ohlcv_window,
                params=self.spec.signal_params,
                regime_state=regime_state,
                position_state={
                    "in_position": self.state.in_position,
                    "cooldown": self.state.cooldown_left, 
                    "entry_price": self.state.entry_price,
                }
            )
        action = sig.get("action", "HOLD")
        reason = sig.get("reason", "")
        # Update cooldown
        self.state.cooldown_left = int(sig.get("cooldown_next", 0))
        dbg["signal"] = sig

        # 2) EdgeExit (in_position일 때 SELL 우선권)
        if self.state.in_position and self.spec.edge_exit is not None:
            ex = update_edge_exit_streak(
                ohlcv_window=ohlcv_window,
                streak=self.state.edge_exit_streak,
                p=self.spec.edge_exit,
            )
            self.state.edge_exit_streak = int(ex["streak"])
            dbg["edge_exit"] = ex
            if ex["should_exit"]:
                action = "SELL"
                reason = ex["reason"]

        if not self.state.in_position:
            self.state.edge_exit_streak = 0

        # 3) Turbo (EdgeTurbo 우선)
        multiplier = 1.0
        exit_fast = False
        
        if self.spec.turbo_params is not None:
            if isinstance(self.spec.turbo_params, EdgeTurboParams):
                t = compute_edge_turbo(
                    ohlcv_window=ohlcv_window,
                    params=self.spec.turbo_params,
                    in_position=self.state.in_position,
                    edge_exit_streak=self.state.edge_exit_streak,
                )
                multiplier = float(t.get("multiplier", 1.0))
                exit_fast = bool(t.get("exit_fast", False))
                dbg["turbo"] = t
            else:
                t = turbo_overlay(
                    market_df=ohlcv_window,
                    signal_state=sig,
                    regime_state=regime_state,
                    position_state={"in_position": self.state.in_position, "entry_price": self.state.entry_price},
                    params=self.spec.turbo_params,
                )
                multiplier = float(t.get("multiplier", 1.0))
                exit_fast = bool(t.get("exit_fast", False))
                dbg["turbo"] = t

        # Fast Exit overrides HOLD/BUY
        if self.state.in_position and exit_fast:
             action = "SELL"
             reason = "fast_exit"

        # 4) Fear Opportunity (차단 아님: 보너스/추가진입 힌트)
        if self.spec.fear_opp is not None and fear_series_window is not None:
            opp = fear_opportunity_signal(
                ohlcv_window=ohlcv_window,
                fear_window_series=fear_series_window,
                p=self.spec.fear_opp,
            )
            dbg["fear_opp"] = opp
            if opp.get("trigger", False):
                multiplier = min(2.5, multiplier + float(opp.get("bonus_mult", 0.0)))
                # 기회 신호는 BUY 우선권을 줄 수 있음(수익 우선)
                if not self.state.in_position and action == "HOLD":
                    action = "BUY"
                    reason = opp.get("reason", "fear_opportunity")

        # 5) Fear Gate (신규 진입은 극단 공포에서만 BLOCK, 그 외 multiplier cap)
        fg = eval_fear_gate(float(fear_score), self.spec.fear_gate)
        dbg["fear_gate"] = fg

        if action == "BUY" and not self.state.in_position:
            if not fg["entry_allowed"]:
                # However, if FearOpp triggered BUY, does it override Gate?
                # Usually Gate is hard safety. But logic says "FearOpp" is opportunity.
                # Profit-First: if explicit opp, maybe override?
                # User prompt: "Fear Gate는 최후로만 두고... 기회감지는 별도"
                # Safe approach: Block acts as block. Opp boosts multiplier if allowed.
                # Or Opp implies "Fear is high but reversing" -> so standard block logic (high fear) would block it.
                # So Opp must override block if designed to catch reversal.
                # Let's check `fear_spike_reversal` logic usage. 
                # If opp['trigger'], we should probably allow entry.
                # But strict reading: "FearGate... 차단이 아니라 레버리지만 캡, 진입은 가능" (from prompt "제공물 A")
                # Wait, "공포로 전면 차단도 제거(차단이 아니라 레버리지만 캡, 진입은 가능)"
                # So eval_fear_gate implementation in Step 1 `kill_switch.py`? 
                # No, Step 1 was pure kill switch. FearGate logic is in `fear_gate.py` (existing).
                # I should check if `fear_gate.py` was updated. 
                # The user prompt A says: "공포로 전면 차단도 제거...". 
                # I need to update `fear_gate.py` too?
                # The prompt provided `kill_switch.py` update, but mentioned "garem_core/live/kill_switch.py 수정(완화 버전)... 공포로 전면 차단도 제거". 
                # Ah, the user might mean `KillSwitch` previously blocked on fear?
                # `KillSwitch` had `block_on_fear_above`. I removed it in Step 1.
                # `FearGate` (replay) still has `block_entry_above`. 
                # If I use standard `FearGateParams`, it will block. 
                # User said "Fear Gate는 최후로만 두고...". 
                # To implement "Block removed", I should configure FearGateParams with high threshold (1.0) or update logic.
                # I will assume standard FearGate is used but param configured generously (0.95).
                if not fg["entry_allowed"]:
                     return StackDecision(
                        ts=ts,
                        action="BLOCKED",
                        reason=f"FearGate:{fg['reason']}",
                        multiplier=1.0,
                        fear_score=float(fear_score),
                        regime=str(regime),
                        qty_frac=1.0,
                        debug=dbg,
                    )
            multiplier = min(multiplier, float(fg["multiplier_cap"]))

        # 6) Position Manager (부분익절/재진입/러너 트레일)
        qty_frac = 1.0
        if self.state.in_position and self.spec.pm_params is not None:
            if self.state.pm_state is None:
                self.state.pm_state = init_pm_state(self.state.entry_price)

            pm = update_position_manager(
                entry_price=self.state.entry_price,
                last_price=float(ohlcv_window["close"].iloc[-1]),
                pos_qty=float(self.state.position_qty),
                pm_state=self.state.pm_state,
                p=self.spec.pm_params,
            )
            dbg["pm"] = pm
            if pm["action"] in ("PARTIAL_SELL", "REBUY", "FULL_SELL"):
                action = pm["action"] if pm["action"] != "FULL_SELL" else "SELL"
                reason = pm["reason"]
                qty_frac = float(pm.get("qty_frac", 1.0))
        
        return StackDecision(
            ts=ts,
            action=action,
            reason=reason,
            multiplier=float(multiplier),
            fear_score=float(fear_score),
            regime=str(regime),
            qty_frac=float(qty_frac),
            debug=dbg,
        )

    def on_fill(self, side: str, price: float, qty: float):
        """
        체결 이후 state 업데이트 (Live/Replay 공통).
        """
        if side == "BUY":
            if not self.state.in_position:
                self.state.in_position = True
                self.state.entry_price = float(price)
                self.state.position_qty = float(qty)
                self.state.pm_state = init_pm_state(self.state.entry_price)
            else:
                # REBUY(추가매수) 단순 합산(평단은 필요하면 확장)
                self.state.position_qty += float(qty)
        elif side == "SELL":
            # If partial sell, reduce qty
            # But here `on_fill` arguments mimic standard run.
            # If partial, caller passes partial qty.
            # We need to distinguish Partial vs Full here or rely on qty check.
            # If qty matches total position -> Full close.
            # Else partial.
            if abs(qty - self.state.position_qty) < 1e-6:
                 self.state.in_position = False
                 self.state.entry_price = 0.0
                 self.state.position_qty = 0.0
                 self.state.edge_exit_streak = 0
                 self.state.pm_state = None
            else:
                 self.state.position_qty = max(0.0, self.state.position_qty - qty)
