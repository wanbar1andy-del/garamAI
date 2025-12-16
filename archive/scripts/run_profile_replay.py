# scripts/run_profile_replay.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

# add project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.config.profile_loader import load_profile_from_yaml


def main():
    project_root = Path(__file__).resolve().parents[1]

    # 입력
    yaml_path = project_root / "reports" / "params_from_modules.yaml"
    if not yaml_path.exists():
        print(f"[ERROR] YAML not found: {yaml_path}")
        print("Please run scripts/map_module_to_params.py first to generate params.")
        sys.exit(1)

    profile_name = sys.argv[1] if len(sys.argv) >= 2 else None
    symbol = sys.argv[2] if len(sys.argv) >= 3 else "005930"
    timeframe = sys.argv[3] if len(sys.argv) >= 4 else "minute"
    tz = sys.argv[4] if len(sys.argv) >= 5 else "Asia/Seoul"

    if not profile_name:
        # Show available profiles if possible
        import yaml
        try:
             data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
             sets = list(data.get("params_sets", {}).keys())
             print(f"Available profiles: {sets}")
        except:
             pass
        print("Usage: python scripts/run_profile_replay.py <profile_name> [symbol] [timeframe] [tz]")
        sys.exit(1)

    print(f"Running Replay: Profile={profile_name}, Symbol={symbol}...")
    try:
        prof = load_profile_from_yaml(yaml_path, profile_name)
    except Exception as e:
        print(f"[ERROR] Failed to load profile '{profile_name}': {e}")
        sys.exit(1)

    res = run_replay(
        project_root=project_root,
        replay=ReplaySpec(
            symbol=symbol,
            timeframe=timeframe,
            timezone=tz,
            fill=prof.fill,
            cost=prof.cost,
            warmup_bars=300,
        ),
        regime_params=RegimeParams(),
        signal_params=prof.signal_params,
        turbo_params=prof.turbo_params,
        initial_equity=100_000_000.0,
        collect_debug=False,
        # FearGate needs to be passed explicitly if not embedded in replay spec logic update
        # We updated run_replay to take fear_gate arg
        fear_gate=prof.fear_gate,
    )

    out = {
        "profile": profile_name,
        "symbol": symbol,
        "timeframe": timeframe,
        "return": res.metrics["total_return"],
        "mdd": res.metrics["max_drawdown"],
        "trades": len(res.trades),
    }

    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "profile_replay_result.csv"
    # Append if exists? Or overwrite? User said save result. Let's overwrite for clean single run result.
    df = pd.DataFrame([out])
    df.to_csv(out_path, index=False, encoding="utf-8")

    print("[OK] profile replay done")
    print(df)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
