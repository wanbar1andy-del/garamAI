# scripts/run_live_safe.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

# add project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.config.profile_loader import load_profile_from_yaml
from garam_core.live.live_runner import LiveRunner
from garam_core.live.order_router import OrderRouter, Order
from garam_core.live.kill_switch import KillSwitchParams, KillSwitchState, eval_kill_switch
from garam_core.live.execution_guard import ExecutionGuardParams, guard_position_size
from garam_core.engine.regime import RegimeParams
from garam_core.data.loader import load_ohlcv, LoadSpec
from garam_core.data.feature_loader import load_fear_feature, align_fear_to_market


def main():
    project_root = Path(__file__).resolve().parents[1]
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_live_safe.py <profile_name> [symbol]")
        sys.exit(1)
        
    profile = sys.argv[1]
    symbol = sys.argv[2] if len(sys.argv) >= 3 else "005930"

    yaml_path = project_root / "reports" / "params_from_modules.yaml"
    if not yaml_path.exists():
         print(f"[ERROR] Params missing: {yaml_path}")
         return

    prof = load_profile_from_yaml(yaml_path, profile)

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
    fear = align_fear_to_market(ohlcv, fear_df)

    runner = LiveRunner(
        signal_params=prof.signal_params,
        turbo_params=prof.turbo_params,
        regime_params=RegimeParams(),
        fear_gate=prof.fear_gate,
    )

    router = OrderRouter()
    ks_params = KillSwitchParams() # Use defaults or load from config if needed
    ks_state = KillSwitchState()
    eg_params = ExecutionGuardParams()

    equity = 100_000_000.0
    window = 300
    logs = []
    
    print(f"Starting SAFE LIVE run on {symbol} (Profile: {profile})...")
    print(f"Live Mode: {router.enable_live}")

    for i in range(window, len(ohlcv)):
        w = ohlcv.iloc[i - window : i + 1]
        ts = w.index[-1]
        price = float(w["close"].iloc[-1])
        
        fs = 0.5
        if ts in fear.index:
            fs = float(fear.loc[ts, "fear_score"])

        # 1. Kill Switch Check
        ks = eval_kill_switch(ks_state, ks_params, fs)
        if not ks["allowed"]:
            logs.append({
                "ts": ts, "action": "HALT", "reason": ks["reason"]
            })
            if ks_state.halted:
                print(f"[HALT] Kill Switch Triggered! Reason: {ks['reason']}")
                break
            continue

        # 2. Strategy Decision
        decision = runner.on_bar(ts, w, fs)

        # 3. Execution Logic
        if decision.action == "BUY":
            qty = guard_position_size(
                equity=equity,
                price=price,
                multiplier=decision.multiplier,
                params=eg_params,
            )
            res = router.send(Order(
                side="BUY",
                qty=qty,
                price=price,
                reason=decision.reason,
            ))
            logs.append({"ts": ts, "action": "BUY", "qty": qty, "mode": res["mode"], "reason": decision.reason})

        elif decision.action == "SELL":
            res = router.send(Order(
                side="SELL",
                qty=0.0,
                price=price,
                reason=decision.reason,
            ))
            logs.append({"ts": ts, "action": "SELL", "mode": res["mode"], "reason": decision.reason})
        
        # (Optional) Update kill switch state pnl if we had trade tracking here
        # For simulation, we'd need to simulate PnL. In real live loop, we read PnL from broker.
        # This script just flows through history safely.

    out = pd.DataFrame(logs)
    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "live_safe_log.csv"
    out.to_csv(out_path, index=False)
    print(f"[OK] Live SAFE run completed: {out_path}")


if __name__ == "__main__":
    main()
