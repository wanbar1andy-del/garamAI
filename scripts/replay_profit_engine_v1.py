# scripts/replay_profit_engine_v1.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

from garam_core.engine.signal_profit_first import ProfitFirstSignalParams
from garam_core.engine.turbo_edge import EdgeTurboParams
from garam_core.engine.exit_edge import EdgeExitParams
from garam_core.engine.position_manager import PositionManagerParams
from garam_core.engine.fear_opportunity import FearOpportunityParams


def main():
    project_root = Path(__file__).resolve().parents[1]
    symbol = sys.argv[1] if len(sys.argv) >= 2 else "005930"

    fill = FillSpec(method="NEXT_OPEN")
    cost = CostModel(commission_rate=0.00015, slippage_rate=0.00025, sell_tax_rate=0.00230)

    print(f"Running Profit Engine V1 on {symbol}...")
    res = run_replay(
        project_root=project_root,
        replay=ReplaySpec(
            symbol=symbol, timeframe="minute", timezone="Asia/Seoul",
            max_bars=20000, warmup_bars=300,
            fill=fill, cost=cost
        ),
        regime_params=RegimeParams(),
        signal_params=ProfitFirstSignalParams(
            momentum_n=60, threshold_min=0.003, threshold_max=0.03, cooldown_bars=0
        ),
        turbo_params=None,  # turbo_edge를 쓰므로 standard turbo는 None
        edge_turbo=EdgeTurboParams(),
        edge_exit=EdgeExitParams(edge_exit_th=0.25, confirm_bars=3),
        pm_params=PositionManagerParams(tp1=0.006, tp2=0.012, trail_from_peak=0.006),
        fear_opp=FearOpportunityParams(),
        initial_equity=100_000_000.0,
        collect_debug=True, # Collect debug to verify components working
    )

    print("Metrics:", res.metrics)
    print("Trades:", len(res.trades))

    out_path = project_root / "reports" / f"profit_engine_v1_{symbol}.csv"
    if res.trades:
        pd.DataFrame(res.trades).to_csv(out_path, index=False, encoding="utf-8")
    else:
        pd.DataFrame([]).to_csv(out_path)
        
    print(f"Saved trades: {out_path}")
    
    # Debug snippet
    if res.debug_rows and len(res.debug_rows) > 0:
         print("Last Debug Row:", res.debug_rows[-1])


if __name__ == "__main__":
    main()
