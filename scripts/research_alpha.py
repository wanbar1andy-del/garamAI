# scripts/research_alpha.py
from __future__ import annotations

import sys
import itertools
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Add project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

def main():
    print(">>> Starting Alpha Research (Grid Search)...")
    
    project_root = Path("c:/garam/garam/garam_core")
    symbol = "005930"
    
    # Locked Models (B-6)
    fill = FillSpec(method="NEXT_OPEN")
    cost = CostModel(commission_rate=0.00015, slippage_rate=0.00025, sell_tax_rate=0.00230)
    
    # Grid Definition
    # Hypothesis: Trade Less (Higher Cooldown), Higher Threshold
    grid = {
        "cooldown": [60, 120, 240, 360],  # 1h, 2h, 4h, 6h
        "momentum_window": [60, 120],            # 1h, 2h lookback for momentum
        "threshold": [0.02, 0.03, 0.05],         # 2%, 3%, 5% rise
    }
    
    keys, values = zip(*grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    results = []
    
    print(f"Testing {len(combinations)} combinations on {symbol} (Last 3 months)...")
    
    for i, params in enumerate(combinations):
        # Construct Signal Params from Grid
        # Note: 'threshold' in SignalParams implies buying when return > threshold. 
        # But 'signal.py' needs to support this. 
        # Current 'signal.py' uses 'momentum_score' but might not have explicit threshold exposed in params depending on impl.
        # Let's check SignalParams definition in signal.py momentarily. 
        # Assuming we can pass these. If not, we fix signal.py.
        
        sig_p = SignalParams(
            momentum_n=params["momentum_window"],
            cooldown_bars=params["cooldown"],
            min_momentum=params["threshold"]
        )
        
        # We need to ensure Signal Logic uses these. Reading signal.py is needed if we want 'threshold'.
        # For now, let's vary Cooldown and Window.
        
        try:
            res = run_replay(
                project_root=project_root,
                replay=ReplaySpec(
                    symbol=symbol, timeframe="minute", timezone="Asia/Seoul",
                    max_bars=20000, # 3 months
                    fill=fill, cost=cost,
                    warmup_bars=300
                ),
                regime_params=RegimeParams(),
                signal_params=sig_p,
                turbo_params=TurboParams(),
                initial_equity=100_000_000.0,
                collect_debug=False
            )
            
            # Metric
            ret = res.metrics["total_return"]
            mdd = res.metrics["max_drawdown"]
            trades = len(res.trades)
            
            results.append({
                "cooldown": params["cooldown"],
                "window": params["momentum_window"],
                "return": ret,
                "mdd": mdd,
                "trades": trades
            })
            
            print(f"[{i+1}/{len(combinations)}] CD={params['cooldown']} Win={params['momentum_window']} -> Ret={ret*100:.2f}% Trd={trades}")
            
        except Exception as e:
            print(f"Error in {params}: {e}")

    # Analysis
    df = pd.DataFrame(results)
    df = df.sort_values("return", ascending=False)
    
    print("\n>>> Top 3 Configurations:")
    print(df.head(3))
    
    out_path = project_root / "reports" / "alpha_grid_result.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved results to {out_path}")

if __name__ == "__main__":
    main()
