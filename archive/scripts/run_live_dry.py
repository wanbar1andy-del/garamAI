# scripts/run_live_dry.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

# add project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.config.profile_loader import load_profile_from_yaml
from garam_core.live.live_runner import LiveRunner
from garam_core.engine.regime import RegimeParams
from garam_core.data.loader import load_ohlcv, LoadSpec
from garam_core.data.feature_loader import load_fear_feature, align_fear_to_market


def main():
    project_root = Path(__file__).resolve().parents[1]

    if len(sys.argv) < 2:
        print("Usage: python scripts/run_live_dry.py <profile_name> [symbol]")
        sys.exit(1)

    profile = sys.argv[1]
    symbol = sys.argv[2] if len(sys.argv) >= 3 else "005930"

    # Load profile
    yaml_path = project_root / "reports" / "params_from_modules.yaml"
    if not yaml_path.exists():
        print(f"[ERROR] Params file missing: {yaml_path}")
        return

    prof = load_profile_from_yaml(yaml_path, profile)

    # Load data
    ohlcv = load_ohlcv(
        project_root / "GARAM_Data",
        symbol,
        "minute",
        LoadSpec(tz="Asia/Seoul"),
    )

    fear_df = load_fear_feature(
        project_root / "GARAM_Data",
        "minute",
        "MARKET",
    )
    # Align fear to market data
    fear = align_fear_to_market(ohlcv, fear_df)

    runner = LiveRunner(
        signal_params=prof.signal_params,
        turbo_params=prof.turbo_params,
        regime_params=RegimeParams(),
        fear_gate=prof.fear_gate,
    )

    # Live-like loop
    window_size = 300 # Enough for signal calc
    logs = []
    
    print(f"Starting DRY-RUN on {symbol} with profile {profile}...")
    
    # Iterate from window_size to end
    for i in range(window_size, len(ohlcv)):
        w = ohlcv.iloc[i - window_size : i + 1] # window including current bar (i)
        ts = w.index[-1]
        
        # Get fear score for this timestamp
        fs = 0.5
        if ts in fear.index:
            fs = float(fear.loc[ts, "fear_score"])

        d = runner.on_bar(ts, w, fs)
        
        logs.append({
            "ts": ts,
            "action": d.action,
            "multiplier": d.multiplier,
            "fear": d.fear_score,
            "regime": d.regime,
            "reason": d.reason,
        })
        
        if i % 1000 == 0:
            print(f"Processed {i}/{len(ohlcv)} bars...", end="\r")

    print(f"Processed {len(ohlcv)}/{len(ohlcv)} bars. Done.")

    out = pd.DataFrame(logs)
    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "live_dry_log.csv"
    out.to_csv(out_path, index=False)
    print(f"[OK] Live DRY-RUN completed: {out_path}")


if __name__ == "__main__":
    main()
