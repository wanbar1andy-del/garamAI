# garam_core/replay/replay_runner.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pandas as pd

from garam_core.health.gate import (
    gate_environment,
    gate_schema,
    gate_determinism,
    gate_strategy_sanity,
    GateSpec,
)
from garam_core.data.loader import load_ohlcv, LoadSpec
from garam_core.engine.regime import classify_regime, RegimeParams
from garam_core.engine.signal import decide_signal, SignalParams
from garam_core.engine.turbo import turbo_overlay, TurboParams
from garam_core.engine.state import PositionState

# B-6 Upgrades
from garam_core.execution.fill_model import FillSpec, get_fill_price
from garam_core.execution.cost_model import CostModel, Side
from garam_core.config.profile_loader import load_strategy_profile
from garam_core.data.feature_loader import load_fear_feature, align_fear_to_market
from garam_core.risk.fear_gate import FearGateParams, eval_fear_gate

# Profit-First Engine Components (Optional)
from garam_core.engine.signal_profit_first import ProfitFirstSignalParams, decide_signal_profit_first
from garam_core.engine.turbo_edge import EdgeTurboParams, compute_edge_turbo
from garam_core.engine.exit_edge import EdgeExitParams, update_edge_exit_streak
from garam_core.engine.position_manager import (
    PositionManagerParams, PositionManagerState, init_pm_state, update_position_manager
)
from garam_core.engine.fear_opportunity import FearOpportunityParams, fear_opportunity_signal
from garam_core.live.kill_switch import KillSwitchParams, KillSwitchState, eval_kill_switch

SignalLike = Union[SignalParams, ProfitFirstSignalParams]
TurboLike = Union[TurboParams, EdgeTurboParams]


@dataclass(frozen=True)
class ReplaySpec:
    symbol: str
    timeframe: str  # "minute" | "daily" 등을
    timezone: str = "UTC"

    # warmup bars
    warmup_bars: int = 80

    # execution policy
    execution_lag_bars: int = 1

    # exposure base
    base_multiplier: float = 1.0

    # Diagnostic limit
    max_bars: Optional[int] = None
    
    # B-6 additions
    fill: FillSpec = FillSpec(method="NEXT_OPEN")
    cost: CostModel = CostModel(
        commission_rate=0.00015,
        slippage_rate=0.00020,
        sell_tax_rate=0.00000,
    )


@dataclass
class ReplayResult:
    trades: List[Dict[str, Any]]
    equity_curve: pd.Series
    metrics: Dict[str, Any]
    debug_rows: List[Dict[str, Any]]


def _compute_metrics(equity: pd.Series) -> Dict[str, Any]:
    if len(equity) == 0:
        return {"total_return": 0.0, "max_drawdown": 0.0}

    total_return = float(equity.iloc[-1] / max(1e-12, equity.iloc[0]) - 1.0)
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    max_dd = float(dd.min())
    return {"total_return": total_return, "max_drawdown": max_dd}


def run_replay(
    project_root: Path,
    replay: ReplaySpec,
    regime_params: RegimeParams = RegimeParams(),
    signal_params: Optional[SignalLike] = None,
    turbo_params: Optional[TurboLike] = None,
    profile_name: Optional[str] = None,
    fear_gate: Optional[FearGateParams] = None,
    initial_equity: float = 1.0,
    collect_debug: bool = True,
    # New Profit-First Components
    edge_turbo: Optional[EdgeTurboParams] = None,
    edge_exit: Optional[EdgeExitParams] = None,
    pm_params: Optional[PositionManagerParams] = None,
    fear_opp: Optional[FearOpportunityParams] = None,
    kill_switch: Optional[KillSwitchParams] = None,
) -> ReplayResult:
    """
    Polymorphic Replay Runner.
    Supports standard Engine params AND Profit-First components.
    """
    # Profile Loading (Switchable Logic)
    if signal_params is None and turbo_params is None and edge_turbo is None and profile_name:
        prof = load_strategy_profile(project_root / "garam_core/config/strategy_profile.yaml", profile_name)
        if signal_params is None:
            signal_params = prof.signal
        if turbo_params is None:
            turbo_params = prof.turbo
        cost_model = prof.cost
        # prof doesn't carry edge_turbo/pm_params yet standardly, but could if extended.
        # Here we assume manual injection for profit engine research or standard profile loaded
    else:
        cost_model = replay.cost

    # Gate0
    paths = gate_environment(project_root)

    # Load Data
    df_raw = load_ohlcv(
        data_root=paths.data_root,
        symbol=replay.symbol,
        timeframe=replay.timeframe,
        spec=LoadSpec(tz=replay.timezone),
    )
    df = gate_schema(df_raw, GateSpec(timezone=replay.timezone))
    
    # [Phase 11-0 Fix] Enforce DatetimeIndex to prevent 1970/Integer timestamps
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Ensure TZ-aware (UTC or Target)
    if df.index.tz is None:
        if replay.timezone == "UTC":
            df.index = df.index.tz_localize("UTC")
        else:
             # Assume naive data matches target timezone
             df.index = df.index.tz_localize(replay.timezone)

    # [DEBUG Phase 11-0] Verify Index
    print(f"[DEBUG-REPLAY] Index Type after Fix: {type(df.index)}")
    print(f"[DEBUG-REPLAY] Index Head: {df.index[:5]}")
    
    # Load Fear if needed
    fear_aligned = None
    if fear_gate or fear_opp:
         try:
             fd = load_fear_feature(paths.data_root, replay.timeframe, "MARKET")
             fear_aligned = align_fear_to_market(df, fd)
         except Exception:
             pass # Graceful degradation if fear missing? Or fail? Prompt implied safe handling

    # state
    pos = PositionState(in_position=False, entry_price=None, cooldown=0)
    
    # Profit First States
    edge_exit_streak = 0
    pm_state: Optional[PositionManagerState] = None
    ks_state = KillSwitchState(peak_equity=initial_equity, equity=initial_equity, halted=False)

    equity = initial_equity
    equity_curve = []
    equity_index = []

    pending_orders: List[Dict[str, Any]] = [] # list of {side, mult, qty_frac, reason}

    trades: List[Dict[str, Any]] = []
    debug_rows: List[Dict[str, Any]] = []

    n = len(df)
    if replay.max_bars is not None:
        n = min(n, replay.warmup_bars + replay.max_bars)

    start = replay.warmup_bars
    lag = replay.execution_lag_bars
    if lag != 1:
        raise ValueError("v0.1 supports execution_lag_bars=1 only.")

    current_pos_size_mult = 0.0 # Multiplier equivalent held. Not strictly tracked in standard pos state.
    # Standard pos state only tracks in_position boolean and entry_price.
    # For PM with partial exits, we need to track sizing fraction.
    # Helper: Let's assume standard pos.in_position means > 0 size.
    # We will track `held_fraction` (0.0 to 1.0 relative to entry size)
    held_fraction = 0.0
    active_multiplier = 1.0 # The leverage mult used at entry.

    for i in range(start, n - 1):
        window = df.iloc[: i + 1]
        ts = window.index[-1]
        next_ts = df.index[i + 1]
        # [Phase 11-0 Fix] Use ISO format globally
        ts_str = next_ts.isoformat() if hasattr(next_ts, 'isoformat') else str(next_ts)
        next_bar = df.iloc[i + 1]
        
        cost_this_bar = 0.0

        # 1. Update Equity (Mark to Market)
        r = float(df["close"].iloc[i + 1] / max(1e-12, df["close"].iloc[i]) - 1.0)
        
        # Kill Switch Update
        if kill_switch:
            ks_state.update(equity)
            ks_res = eval_kill_switch(ks_state, kill_switch)
            if not ks_res["allowed"]:
                # Force exit if in position?
                if pos.in_position:
                    # Treat as pending exit for next bar or immediate?
                    # Rule says "Stop". Simulation stops or just exits? Usually exit first.
                    pending_orders.append({"side": "SELL", "reason": "KILL_SWITCH"})
        
        if pos.in_position:
            # Effective exposure = active_multiplier * held_fraction
            equity *= (1.0 + r * active_multiplier * held_fraction)

        # 2. Execute Pending Orders
        # Process SELLs first, then BUYs
        # Sort pending: SELL first
        pending_orders.sort(key=lambda x: 0 if x["side"] == "SELL" else 1)
        
        executed_orders = []
        for order in pending_orders:
            side = order["side"]
            reason = order.get("reason", "")
            
            if side == "SELL":
                 if pos.in_position:
                     qty_frac = order.get("qty_frac", 1.0) # 1.0 is full sell
                     exit_price = get_fill_price(next_bar, replay.fill, side="SELL")
                     
                     # [B-6 Fix] Cost applied to Notional Value (Equity * Multiplier * Fraction)
                     # Old: equity *= (1.0 - cost_model.cost_rate("SELL") * held_fraction * qty_frac) - This was equity penalty
                     # New: Deduct Cost = Notional * Rate
                     
                     trade_exposure = active_multiplier * held_fraction * qty_frac
                     cost_amt = equity * trade_exposure * cost_model.cost_rate("SELL")
                     equity -= cost_amt
                     cost_this_bar += cost_amt
                     
                     equity = max(0.0, equity) # [B-6 Safety] Protection
                     
                     # [Phase 11-0 Fix] Use ISO format
                     ts_str = next_ts.isoformat() if hasattr(next_ts, 'isoformat') else str(next_ts)
                     
                     trades.append({
                         "type": "EXIT", "ts": ts_str, "price": exit_price, 
                         "multiplier": active_multiplier, "frac": qty_frac, "reason": reason
                     })
                     
                     held_fraction -= (held_fraction * qty_frac) # Reduce held fraction
                     if held_fraction < 1e-6:
                         pos.in_position = False
                         pos.entry_price = None
                         held_fraction = 0.0
                         active_multiplier = 1.0
                         pm_state = None # Reset PM state

            elif side == "BUY":
                 # Entry or Re-entry
                 # Check Fear Gate for Entry Block
                 block = False
                 fg_res = None
                 if fear_gate and fear_aligned is not None and ts in fear_aligned.index:
                      fs = float(fear_aligned.loc[ts, "fear_score"])
                      fg_res = eval_fear_gate(fs, fear_gate)
                      if not fg_res["entry_allowed"]:
                           block = True
                 
                 # Also check Kill Switch block
                 if ks_state.halted:
                     block = True

                 if not block:
                     mult = order.get("mult", replay.base_multiplier)
                     
                     # Fear Gate Cap
                     if fg_res:
                         mult = min(mult, fg_res["multiplier_cap"])

                     entry_price = get_fill_price(next_bar, replay.fill, side="BUY")
                     qty_frac = order.get("qty_frac", 1.0) 
                     
                     if not pos.in_position:
                         # New Entry
                         # [B-6 Fix] Cost on Notional (Equity * Multiplier)
                         cost_amt = equity * mult * cost_model.cost_rate("BUY")
                         equity -= cost_amt
                         cost_this_bar += cost_amt
                         
                         equity = max(0.0, equity) # [B-6 Safety]
                         
                         pos.in_position = True
                         pos.entry_price = entry_price
                         active_multiplier = mult
                         held_fraction = 1.0
                         pm_state = init_pm_state(entry_price)
                         trades.append({
                             "type": "ENTER", "ts": ts_str, "price": entry_price, 
                             "multiplier": mult, "reason": reason
                         })
                     else:
                         # Re-entry / Pyramiding (PM REBUY)
                         # [B-6 Fix] Cost on Notional Added
                         trade_exposure = active_multiplier * qty_frac
                         cost_amt = equity * trade_exposure * cost_model.cost_rate("BUY")
                         equity -= cost_amt
                         cost_this_bar += cost_amt
                         
                         equity = max(0.0, equity) # [B-6 Safety]
                         
                         held_fraction = min(1.0, held_fraction + qty_frac) # Cap at 100% logic for now
                         trades.append({
                             "type": "REBUY", "ts": ts_str, "price": entry_price,
                             "frac": qty_frac, "reason": reason
                         })

        pending_orders = [] # Clear orders after processing

        if equity <= 0 or (equity != equity):
             break
             
        equity_curve.append(equity)
        equity_index.append(next_ts)

        # --- Decision Logic (Bar i) ---
        
        # 1. Data Prep
        regime_state = classify_regime(window, regime_params)
        
        # Fear/Edge Prep
        fs = 0.5
        if fear_aligned is not None and ts in fear_aligned.index:
            fs = float(fear_aligned.loc[ts, "fear_score"])
        
        # 2. Signal
        # Use duck typing to avoid import/reload instance check failures
        if hasattr(signal_params, "threshold_min"):
            signal_state = decide_signal_profit_first(
                ohlcv_window=window,
                params=signal_params,
                in_position=pos.in_position,
                cooldown_left=pos.cooldown,
            )
        else:
            signal_state = decide_signal(
                window,
                regime_state=regime_state,
                params=signal_params,
                position_state={
                    "in_position": pos.in_position,
                    "cooldown": pos.cooldown,
                    "entry_price": pos.entry_price,
                },
            )
        
        pos.cooldown = int(signal_state["cooldown_next"])
        action = signal_state["action"]
        reason = signal_state.get("reason", "")

        # 3. Position Manager Updates (Intermediate Actions: PARTIAL, REBUY, FULL_SELL)
        pm_action = None
        if pos.in_position and pm_params and pm_state:
             pm_res = update_position_manager(
                 entry_price=pos.entry_price,
                 last_price=float(window["close"].iloc[-1]),
                 pos_qty=held_fraction, # surrogate
                 pm_state=pm_state,
                 p=pm_params
             )
             if pm_res["action"] != "HOLD":
                 pm_action = pm_res
                 # If full sell, override action
                 if pm_res["action"] == "FULL_SELL":
                     action = "SELL"
                     reason = pm_res["reason"]

        # 4. Exit Edge Logic (Force Sell)
        if pos.in_position and edge_exit:
             ex_res = update_edge_exit_streak(window, edge_exit_streak, edge_exit)
             edge_exit_streak = int(ex_res["streak"])
             if ex_res["should_exit"]:
                 action = "SELL"
                 reason = ex_res["reason"]
        elif not pos.in_position:
             edge_exit_streak = 0

        # 5. Turbo / EdgeTurbo
        multiplier = 1.0
        exit_fast = False
        
        if edge_turbo:
             t_res = compute_edge_turbo(window, edge_turbo, pos.in_position, edge_exit_streak)
             multiplier = float(t_res["multiplier"])
             exit_fast = bool(t_res.get("exit_fast", False))
        elif turbo_params:
             t_res = turbo_overlay(
                window,
                signal_state=signal_state,
                regime_state=regime_state,
                position_state={"in_position": pos.in_position, "entry_price": pos.entry_price},
                params=turbo_params
             )
             multiplier = float(t_res["multiplier"])
             exit_fast = bool(t_res["exit_fast"])
             
             # [B-6 Fix] Turbo fast-exit must trigger cooldown to prevent immediate re-entry
             if exit_fast:
                 # Try to extract cooldown, default to 60 if not found
                 cd = getattr(signal_params, "cooldown_bars", 60)
                 pos.cooldown = max(pos.cooldown, cd)

        # 6. Fear Opportunity (Bonus Mult / Entry Trigger)
        if fear_opp and fear_aligned is not None:
             opp = fear_opportunity_signal(window, fear_aligned["fear_score"], fear_opp)
             if opp["trigger"]:
                 multiplier += opp["bonus_mult"] # Bonus
                 # If holding or blocked, maybe opportunity unlocks entry?
                 # Strategy Choice: Opp can trigger BUY if action was HOLD
                 if not pos.in_position and action == "HOLD":
                      action = "BUY"
                      reason = opp["reason"]

        # Cap Multiplier
        # (Already handled by turbo/fear logic mostly, but simple clamp here safety)
        multiplier = min(multiplier, 2.5) # Global max cap

        # --- Scheduling Orders ---
        
        # Priority: Exits first
        if pos.in_position:
             if action == "SELL" or exit_fast:
                  pending_orders.append({"side": "SELL", "reason": reason, "qty_frac": 1.0})
             elif pm_action:
                  if pm_action["action"] == "PARTIAL_SELL":
                       pending_orders.append({"side": "SELL", "reason": pm_action["reason"], "qty_frac": pm_action["qty_frac"]})
                  elif pm_action["action"] == "REBUY":
                       pending_orders.append({"side": "BUY", "reason": pm_action["reason"], "qty_frac": pm_action["qty_frac"], "mult": multiplier})
        
        if (not pos.in_position) and action == "BUY":
             pending_orders.append({"side": "BUY", "mult": multiplier, "reason": reason})

        # [Phase 12 Compatibility] Capture Veto Reasons
        veto_reason = None
        
        # Check explicit blocks for potential entries
        if action == "BUY" and not pos.in_position:
             # Fear Gate Check
             if fear_gate and fear_aligned is not None:
                  if ts in fear_aligned.index:
                      fs_val = float(fear_aligned.loc[ts, "fear_score"])
                      fg_res = eval_fear_gate(fs_val, fear_gate)
                      if not fg_res["entry_allowed"]:
                          veto_reason = "FEAR_GATE_BLOCK"
             
             # Kill Switch Check
             if ks_state.halted:
                 veto_reason = "KILL_SWITCH_HALT"

        if collect_debug:
             debug_rows.append({
                 "ts": str(ts),
                 "equity": equity,
                 "pos": pos.in_position,
                 "held": held_fraction,
                 "action": action,
                 "mult": multiplier,
                 "fear": fs,
                 "cost": cost_this_bar,
                 # [Conflict Report Fields]
                 "regime": regime_state.get("regime", "UNKNOWN"),
                 "entry_signal": (action == "BUY"),
                 "veto_reason": veto_reason,
                 "final_reason": reason
             })

    equity_series = pd.Series(equity_curve, index=pd.DatetimeIndex(equity_index), name="equity")
    metrics = _compute_metrics(equity_series)

    return ReplayResult(
        trades=trades,
        equity_curve=equity_series,
        metrics=metrics,
        debug_rows=debug_rows,
    )
