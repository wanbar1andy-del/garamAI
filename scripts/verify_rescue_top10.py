# scripts/verify_rescue_top10.py
# RESCUE_EXPANSION_TOP10
# Date: 2025-12-15
# Purpose: Verify Rescue Baseline on Top 10 Liquid Assets (Generalization Test)

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import traceback

# Allow importing from parent
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

# Top 10 Liquid Symbols (Representative Mix: Tech, Auto, Battery, Bank, Platform)
TOP_10_SYMBOLS = [
    "005930", # Samsung Elec
    "000660", # SK Hynix
    "373220", # LG Energy Sol
    "207940", # Samsung Biologics
    "005380", # Hyundai Motor
    "000270", # Kia
    "005490", # POSCO Holdings
    "035420", # NAVER
    "006400", # Samsung SDI
    "051910", # LG Chem
]

def find_project_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(10):
        # 1. Check if 'garam_core' is present here (Repo Root)
        if (p / "garam_core" / "config" / "paths.yaml").exists():
            return p / "garam_core"
        # 2. Check if we are inside garam_core (Module Root)
        if (p / "config" / "paths.yaml").exists():
            return p
        p = p.parent
        
    # Fallback
    fallback = Path("c:/garam/garam/garam_core")
    if (fallback / "config" / "paths.yaml").exists():
        return fallback
    raise FileNotFoundError("config/paths.yaml not found.")

def run_single_symbol(symbol, project_root, cost_model, signal_params, regime_params, turbo_params):
    replay_spec = ReplaySpec(
        symbol=symbol,
        timeframe="minute",
        timezone="Asia/Seoul",
        warmup_bars=600,
        fill=FillSpec(method="NEXT_OPEN"),
        cost=cost_model,
        base_multiplier=1.0,
        max_bars=60 * 381, # 60 Days
    )
    
    try:
        res = run_replay(
            project_root=project_root,
            replay=replay_spec,
            regime_params=regime_params,
            signal_params=signal_params,
            turbo_params=turbo_params,
            initial_equity=100_000_000.0,
            collect_debug=True # [Enable for Conflict Report]
        )
        
        # Save Debug Logs for Report
        debug_path = Path(f"results/{symbol}_debug.csv")
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        if res.debug_rows:
            pd.DataFrame(res.debug_rows).to_csv(debug_path, index=False)
        
        metrics = res.metrics
        trades = res.trades
        equity = res.equity_curve
        
        days = pd.Series(equity.index.date).nunique()
        if days == 0: days = 1
        tpd = len(trades) / days
        
        return {
            "symbol": symbol,
            "return": metrics['total_return'],
            "mdd": metrics['max_drawdown'],
            "trades": len(trades),
            "days": days,
            "tpd": tpd,
            "final_equity": equity.iloc[-1] if not equity.empty else 100_000_000.0
        }
        
    except Exception as e:
        print(f"[FAIL] {symbol}: {e}")
        # traceback.print_exc()
        return None

def main():
    print(f">>> STARTING TOP 10 EXPANSION TEST [RESCUE_BASELINE] <<<")
    project_root = find_project_root(Path(__file__))
    print(f"Project Root: {project_root}")
    
    # RESCUE BASELINE PARAMS (LOCKED)
    signal_params = SignalParams(
        cooldown_bars=120,      
        momentum_n=20,          
        min_momentum=0.008,     # 0.8%
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
    cost_real = CostModel(
        commission_rate=0.00015,
        slippage_rate=0.00020, 
        sell_tax_rate=0.00230 
    )
    
    results = []
    print(f"{'Symbol':<10} {'Return':<10} {'MDD':<10} {'Trades':<8} {'TPD':<8}")
    print("-" * 50)
    
    for sym in TOP_10_SYMBOLS:
        res = run_single_symbol(sym, project_root, cost_real, signal_params, regime_params, turbo_params)
        if res:
            results.append(res)
            print(f"{res['symbol']:<10} {res['return']*100:>6.2f}% {res['mdd']*100:>7.2f}% {res['trades']:>8} {res['tpd']:>8.2f}")
        else:
            print(f"{sym:<10} FAILED")

    # Summary
    if results:
        df = pd.DataFrame(results)
        print("=" * 50)
        print(f"AVERAGE RETURN: {df['return'].mean()*100:.2f}%")
        print(f"AVERAGE TPD   : {df['tpd'].mean():.2f}")
        print(f"WIN RATE (Avg>0): {len(df[df['return']>0])}/{len(df)}")
        print("=" * 50)
        
        # Save
        csv_path = Path("results/rescue_top10_summary.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")

if __name__ == "__main__":
    main()
