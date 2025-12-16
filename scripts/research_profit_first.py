# scripts/research_profit_first.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

# 새 시그널
from garam_core.engine.signal_profit_first import ProfitFirstSignalParams


def main():
    project_root = Path(__file__).resolve().parents[1]
    symbol = sys.argv[1] if len(sys.argv) >= 2 else "005930"

    fill = FillSpec(method="NEXT_OPEN")
    cost = CostModel(commission_rate=0.00015, slippage_rate=0.00025, sell_tax_rate=0.00230)

    # 공격형 기본값: 쿨다운 0 (거래 억제 없음)
    sig = ProfitFirstSignalParams(
        momentum_n=60,
        base_threshold=0.01,
        threshold_min=0.003,
        threshold_max=0.03,
        cooldown_bars=0,
    )

    print(f"Running Profit-First Replay on {symbol}...")
    res = run_replay(
        project_root=project_root,
        replay=ReplaySpec(
            symbol=symbol, timeframe="minute", timezone="Asia/Seoul",
            max_bars=20000, warmup_bars=300,
            fill=fill, cost=cost
        ),
        regime_params=RegimeParams(),
        signal_params=sig,               # polymorphic call
        turbo_params=TurboParams(),      # standard turbo for baseline
        initial_equity=100_000_000.0,
        collect_debug=False,
    )

    print(f"Metrics: {res.metrics}")
    print(f"Trades: {len(res.trades)}")
    
    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"profit_first_{symbol}.json"
    
    # Save simple JSON
    import json
    with open(out_path, "w") as f:
         json.dump({"metrics": res.metrics, "trades": len(res.trades)}, f)
         
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
