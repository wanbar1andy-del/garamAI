# garam_core/config/profile_loader.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import yaml

from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel
from garam_core.risk.fear_gate import FearGateParams


class ProfileLoadError(RuntimeError):
    pass


@dataclass(frozen=True)
class StrategyProfile:
    name: str
    signal_params: SignalParams
    turbo_params: TurboParams
    fill: FillSpec
    cost: CostModel
    fear_gate: FearGateParams
    
    # Alias properties for compatibility with older code if it accessed .signal or .turbo directly
    @property
    def signal(self) -> SignalParams:
        return self.signal_params

    @property
    def turbo(self) -> TurboParams:
        return self.turbo_params


def _req(d: Dict[str, Any], k: str, ctx: str) -> Any:
    # Helper to optionally get, or raise if strictly needed.
    # For flexibility with partial configs, we might want soft get.
    # User implementation suggested _req implying required? 
    # But usually profiles might omit sections. Let's use get with defaults as per user code logic below.
    # Actually user code uses _req but then .get inside. 
    # Let's follow user's specific logic provided in prompt.
    if k not in d:
        raise ProfileLoadError(f"Missing key '{k}' in {ctx}")
    return d[k]


def load_profile_from_yaml(yaml_path: Path, profile_name: Optional[str] = None) -> StrategyProfile:
    if not yaml_path.exists():
        raise ProfileLoadError(f"Profile yaml not found: {yaml_path}")

    obj = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    
    # Support both "params_sets" (generated) and "profiles" (strategy_profile.yaml)
    sets = obj.get("params_sets", obj.get("profiles", {}))
    
    # If name not provided, try to find active_profile
    if profile_name is None:
        profile_name = obj.get("active_profile")
        if profile_name is None:
             # Fallback to first if available or error
             if sets:
                 profile_name = list(sets.keys())[0]
             else:
                 raise ProfileLoadError("No profile_name provided and no 'active_profile' in yaml.")

    if profile_name not in sets:
        raise ProfileLoadError(f"profile_name not found: {profile_name}. available={list(sets.keys())[:20]}")

    p = sets[profile_name]

    # signal
    # User code used _req(p, "signal") but let's be safe if it's missing (defaults?)
    # Assuming valid profile structure.
    s = p.get("signal", {})
    signal = SignalParams(
        momentum_n=int(s.get("momentum_n", 120)),
        cooldown_bars=int(s.get("cooldown_bars", 240)),
        min_momentum=float(s.get("min_momentum", 0.02)),
        allow_buy_in_neutral=bool(s.get("allow_buy_in_neutral", False)),
        allow_buy_in_bear=bool(s.get("allow_buy_in_bear", False))
    )

    # turbo
    t = p.get("turbo", {})
    turbo = TurboParams(
        target_vol=float(t.get("target_vol", 0.02)),
        fast_exit_drawdown=float(t.get("fast_exit_drawdown", 0.03)),
        max_multiplier=float(t.get("max_multiplier", 2.5)),
        min_multiplier=float(t.get("min_multiplier", 1.0)),
        vol_window=int(t.get("vol_window", 20)),
        vol_floor=float(t.get("vol_floor", 0.002)),
        vol_ceiling=float(t.get("vol_ceiling", 0.10)),
        fast_exit_on_bear=bool(t.get("fast_exit_on_bear", True))
    )

    # execution
    ex = p.get("execution", {})
    fill_method = str(ex.get("fill", "NEXT_OPEN"))
    fill = FillSpec(method=fill_method)
    
    c = ex.get("cost", {})
    cost = CostModel(
        commission_rate=float(c.get("commission_rate", 0.00015)),
        slippage_rate=float(c.get("slippage_rate", 0.00025)),
        sell_tax_rate=float(c.get("sell_tax_rate", 0.00230)),
    )

    # fear gate
    r = p.get("risk", {})
    fg = (r.get("fear_gate") or {})
    fear_gate = FearGateParams(
        enabled=bool(fg.get("enabled", True)),
        block_entry_above=float(fg.get("block_entry_above", 0.85)),
        multiplier_cap=float(fg.get("multiplier_cap", 1.3)),
    )

    return StrategyProfile(
        name=profile_name,
        signal_params=signal,
        turbo_params=turbo,
        fill=fill,
        cost=cost,
        fear_gate=fear_gate,
    )

# Alias for backward compatibility if needed, or for verify script usage
load_strategy_profile = load_profile_from_yaml
