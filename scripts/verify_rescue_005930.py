# scripts/verify_rescue_005930.py
# RESCUE_BASELINE
# Date: 2025-12-15
# Purpose: Verify Turbo v3 Rescue Logic on Single Symbol (005930)
# Validated Parameters: Mom 0.008, CD 120, Regime 120/480

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import traceback

# Allow importing from parent (if run as script)
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

def find_project_root(start: Path) -> Path:
    """
    Robustly find the project root containing config/paths.yaml.
    """
    p = start.resolve()
    # 1. Search upwards
    for _ in range(10):
        if (p / "config" / "paths.yaml").exists():
            return p
        p = p.parent
    
    # 2. Fallback to known safe root
    fallback = Path("c:/garam/garam")
    if (fallback / "config" / "paths.yaml").exists():
        return fallback

    raise FileNotFoundError("config/paths.yaml not found. Check repo root or paths.yaml location.")

def run_test(symbol, project_root, label, cost_model, signal_params, regime_params, turbo_params):
    print(f"\n>>> RUNNING TEST: {label} <<<")
    
    replay_spec = ReplaySpec(
        symbol=symbol,
        timeframe="minute",
        timezone="Asia/Seoul",
        warmup_bars=600, # Sufficient for 480 MA
        fill=FillSpec(method="NEXT_OPEN"),
        cost=cost_model,
        base_multiplier=1.0,
        max_bars=60 * 381, # ~60 Days
    )
    
    try:
        res = run_replay(
            project_root=project_root,
            replay=replay_spec,
            regime_params=regime_params,
            signal_params=signal_params,
            turbo_params=turbo_params,
            initial_equity=100_000_000.0,
            collect_debug=True
        )
    except Exception as e:
        print(f"[FAIL] {label} Failed: {e}")
        traceback.print_exc()
        return

    # Metrics
    metrics = res.metrics
    trades = res.trades
    equity = res.equity_curve
    
    # CORRECTED TPD CALCULATION
    days = pd.Series(equity.index.date).nunique()
    if days == 0: days = 1
    tpd = len(trades) / days
    
    print("-" * 50)
    print(f"[{label}] RESULT")
    print(f"Total Return: {metrics['total_return']*100:.2f}%")
    print(f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
    print(f"Trade Count: {len(trades)}")
    print(f"Days: {days}")
    print(f"TPD: {tpd:.2f}")
    print("-" * 50)

    # Save Debug
    debug_path = Path(f"results/rescue_005930_{label}_debug.csv")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    if res.debug_rows:
        pd.DataFrame(res.debug_rows).to_csv(debug_path, index=False)
        print(f"Saved Debug: {debug_path}")
    
    # Save Equity
    equity.to_csv(f"results/rescue_005930_{label}_equity.csv")

def main():
    print(f">>> STARTING EMERGENCY RESCUE DIAGNOSIS (005930) [RESCUE_BASELINE] <<<")
    
    try:
        project_root = find_project_root(Path(__file__))
        print(f"[INIT] Project Root: {project_root}")
    except FileNotFoundError as e:
        print(f"[CRITICAL] {e}")
        return

    symbol = "005930"
    
    # 1. FIXED RESCUE PARAMS
    signal_params = SignalParams(
        cooldown_bars=120,      
        momentum_n=20,          
        min_momentum=0.008,     # 0.8% Strong Impulse (Rescue Baseline)
        allow_buy_in_neutral=False,
        allow_buy_in_bear=False
    )
    
    regime_params = RegimeParams(
        ma_fast=120,
        ma_slow=480,
        bear_buffer=-0.002
    )
    
    turbo_params = TurboParams(
        max_multiplier=2.0,
        min_multiplier=1.0,
        vol_window=60,
        target_vol=0.001
    )

    # 2. RUN SCENARIOS
    
    # Baseline: Zero Cost (Proof of Alpha)
    cost_zero = CostModel(commission_rate=0.0, slippage_rate=0.0, sell_tax_rate=0.0)
    run_test(symbol, project_root, "ZERO_COST", cost_zero, signal_params, regime_params, turbo_params)

    # Validation: Real Cost (Proof of Profitability)
    cost_real = CostModel(
        commission_rate=0.00015,
        slippage_rate=0.00020, 
        sell_tax_rate=0.00230 
    )
    run_test(symbol, project_root, "REAL_COST", cost_real, signal_params, regime_params, turbo_params)

if __name__ == "__main__":
    main()
