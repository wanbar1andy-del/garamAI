# scripts/verify_generalization.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

# Add project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

def main():
    print(">>> Starting Generalization Test (000660)...")
    
    project_root = Path("c:/garam/garam/garam_core")
    symbol = "000660" # SK Hynix
    
    # Locked Models (B-6)
    fill = FillSpec(method="NEXT_OPEN")
    cost = CostModel(commission_rate=0.00015, slippage_rate=0.00025, sell_tax_rate=0.00230)
    
    # Golden Params from 005930 Optimization
    # Cooldown=240, Window=120, Threshold=0.02
    sig_p = SignalParams(
        momentum_n=120,
        cooldown_bars=240,
        min_momentum=0.02
    )
    
    try:
        res = run_replay(
            project_root=project_root,
            replay=ReplaySpec(
                symbol=symbol, timeframe="minute", timezone="Asia/Seoul",
                max_bars=20000, # 3 months
                fill=fill, cost=cost,
                warmup_bars=300
            ),
            regime_params=RegimeParams(), # Defaults
            signal_params=sig_p,
            turbo_params=TurboParams(),   # Defaults (VolTarget=0.02 is default but strict cost might kill it if not tuned, but we test base signal first)
            initial_equity=100_000_000.0,
            collect_debug=False
        )
        
        metrics = res.metrics
        trades = len(res.trades)
        
        print("-" * 40)
        print(f"Target: {symbol}")
        print(f"Total Return: {metrics['total_return']*100:.2f}%")
        print(f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
        print(f"Trade Count: {trades}")
        print("-" * 40)
        
        if metrics['total_return'] > 0:
            print(">>> RESULT: GENERALIZATION SUCCESS (Profit > 0)")
        else:
            print(">>> RESULT: GENERALIZATION ISSUE (Profit <= 0)")
            
    except Exception as e:
        print(f"[ERROR] Replay Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
