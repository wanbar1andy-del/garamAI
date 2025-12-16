# scripts/verify_alpha_vol_scaled.py
# VOL_SCALED_ALPHA_TEST
# Date: 2025-12-15
# Purpose: Verify Vol-Scaled Momentum and Cooldown logic on Top 10 Symbols.

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Allow importing from parent
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

TOP_10_SYMBOLS = [
    "005930", "000660", "373220", "207940", "005380",
    "000270", "005490", "035420", "006400", "051910",
]

def find_project_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(10):
        if (p / "garam_core" / "config" / "paths.yaml").exists():
            return p / "garam_core"
        if (p / "config" / "paths.yaml").exists():
            return p
        p = p.parent
    fallback = Path("c:/garam/garam/garam_core")
    if (fallback / "config" / "paths.yaml").exists():
        return fallback
    raise FileNotFoundError("config/paths.yaml not found.")

def run_test(experiment_name, signal_params):
    print(f"\n>>> RUNNING EXPERIMENT: {experiment_name} <<<")
    project_root = find_project_root(Path(__file__))
    
    # Common Params
    regime_params = RegimeParams(ma_fast=120, ma_slow=480, bear_buffer=-0.002)
    turbo_params = TurboParams(max_multiplier=2.0)
    cost_model = CostModel(commission_rate=0.00015, slippage_rate=0.00020, sell_tax_rate=0.00230)
    
    results = []
    
    for sym in TOP_10_SYMBOLS:
        replay_spec = ReplaySpec(
            symbol=sym,
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
                collect_debug=True
            )
            
            metrics = res.metrics
            trades = res.trades
            days = pd.Series(res.equity_curve.index.date).nunique()
            if days == 0: days = 1
            tpd = float(len(trades) / days)
            
            row = {
                "symbol": sym,
                "ret": metrics['total_return'],
                "mdd": metrics['max_drawdown'],
                "trades": len(trades),
                "tpd": tpd,
                "win_rate": res.metrics.get("win_rate", 0.0)
            }
            results.append(row)
            print(f"{sym:<8} Ret: {row['ret']*100:>6.2f}% | MDD: {row['mdd']*100:>6.2f}% | TPD: {tpd:.2f} | Win: {row['win_rate']*100:.1f}%")
            
            # Save Debug for analysis
            debug_path = Path(f"results/{experiment_name}/{sym}_debug.csv")
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            if res.debug_rows:
                pd.DataFrame(res.debug_rows).to_csv(debug_path, index=False)
                
        except Exception as e:
            print(f"{sym} FAIL: {e}")

    # Summary
    if results:
        df = pd.DataFrame(results)
        print("-" * 60)
        print(f"AVG RETURN: {df['ret'].mean()*100:.2f}%")
        print(f"AVG TPD   : {df['tpd'].mean():.2f}")
        print(f"WINNERS   : {len(df[df['ret']>0])}/{len(df)}")
        print("-" * 60)
        
        summary_path = Path(f"results/{experiment_name}_summary.csv")
        df.to_csv(summary_path, index=False)

def main():
    # Exp A: Vol-Scaled Momentum Only
    # k = 1.0 (1 stddev of 20min vol). 
    # Valid approximation? 20min Vol ~ 0.2~0.5%? 1.0*Vol ~ 0.2~0.5%.
    # Fixed was 0.8%. So this is LOOSER for low vol, TIGHTER for high vol?
    # Actually 20min stddev is very small. Minute returns are ~0.05-0.1%.
    # Std(20) ~ 0.05%? 
    # Wait, simple validation. 1-min return std is typically 0.05% (5bps).
    # k=1.0 ==> 0.05% threshold. This is VERY LOW compared to 0.8% (80bps).
    # If 0.8% was the 'impulse', then k needs to be ~10-15?
    # Or did user mean "Realized Volatility" annualized logic?
    # User said: "min_momentum = k * std(1min returns, last n)".
    # If std is 0.0005. k=1.0 -> 0.0005 threshold.
    # Fixed was 0.008.
    # So k needs to be ~16 to match the AMPLITUDE of the fixed threshold.
    # User said "k=1.0~2.0 range is sufficient".
    # This implies user thinks 0.008 was WAY too high?
    # Or user assumes Vol is measured differently?
    # No, "std(1min returns)" is small.
    # If user wants k=1.0, they want VERY sensitive momentum.
    # Let's try k=1.0 first, as requested.
    
    # Signal Params Exp A
    params_A = SignalParams(
        cooldown_bars=120, # Fixed
        use_vol_scaled_momentum=True,
        vol_lookback=20,
        min_momentum_k=1.0, # Start with 1.0
        use_vol_scaled_cooldown=False
    )
    
    run_test("EXP_A_VOL_MOM", params_A)

    # Exp B: Add Vol-Scaled Cooldown
    # user "cooldown = base * realized / target" (interpreted intent)
    # base=120, target=0.001 (10bps vol).
    # If vol=5bps -> 120 * 0.5 = 60 bars.
    # If vol=20bps -> 120 * 2.0 = 240 bars.
    params_B = SignalParams(
        # Same Momentum
        use_vol_scaled_momentum=True,
        vol_lookback=20,
        min_momentum_k=1.0,
        # Vol Cooldown
        use_vol_scaled_cooldown=True,
        cooldown_bars=120,
        cooldown_target_vol=0.001 # 0.1% per minute std
    )
    
    run_test("EXP_B_VOL_BOTH", params_B)

if __name__ == "__main__":
    main()
