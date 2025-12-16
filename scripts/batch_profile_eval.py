# scripts/batch_profile_eval.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import yaml

# add project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.config.profile_loader import load_profile_from_yaml


def main():
    project_root = Path(__file__).resolve().parents[1]
    yaml_path = project_root / "reports" / "params_from_modules.yaml"
    
    if not yaml_path.exists():
        print(f"[ERROR] YAML not found: {yaml_path}")
        return

    # 기본 배치
    symbols = ["005930", "000660"]  # Expanded in future to more
    timeframe = "minute"
    tz = "Asia/Seoul"

    # profiles: args로 받거나 전체
    # YAML은 직접 파싱
    y = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    profiles = list((y.get("params_sets") or {}).keys())

    # args로 profile 일부 지정 가능
    if len(sys.argv) >= 2:
        profiles = sys.argv[1].split(",")

    print(f"Starting batch eval for {len(profiles)} profiles on {len(symbols)} symbols...")
    
    rows = []
    for pname in profiles:
        try:
            prof = load_profile_from_yaml(yaml_path, pname)
        except Exception as e:
            print(f"[WARN] Skipping {pname}: load failed {e}")
            continue
            
        for sym in symbols:
            try:
                res = run_replay(
                    project_root=project_root,
                    replay=ReplaySpec(
                        symbol=sym, timeframe=timeframe, timezone=tz,
                        fill=prof.fill, cost=prof.cost,
                        warmup_bars=300,
                    ),
                    regime_params=RegimeParams(),
                    signal_params=prof.signal_params,
                    turbo_params=prof.turbo_params,
                    initial_equity=100_000_000.0,
                    collect_debug=False,
                    fear_gate=prof.fear_gate,
                )
                rows.append({
                    "profile": pname,
                    "symbol": sym,
                    "return": res.metrics["total_return"],
                    "mdd": res.metrics["max_drawdown"],
                    "trades": len(res.trades),
                    "ok": True,
                })
                print(f"  > {pname} @ {sym}: Ret={res.metrics['total_return']:.2%} MDD={res.metrics['max_drawdown']:.2%}")
            except Exception as e:
                rows.append({
                    "profile": pname,
                    "symbol": sym,
                    "ok": False,
                    "error": f"{type(e).__name__}: {e}",
                })
                print(f"  > {pname} @ {sym}: FAIL {e}")

    df = pd.DataFrame(rows)
    if df.empty:
        print("No results generated.")
        return

    # 랭킹(보수): return 높고 mdd 작고 trades 적은 방향
    # Simple score: Return - 0.5*|MDD|
    # Penalty for excessive trades > 1000? Not explicitly, but cost model handles it.
    df_ok = df[df["ok"] == True].copy()
    if len(df_ok) > 0:
        df_ok["score"] = df_ok["return"] - 0.5 * abs(df_ok["mdd"])
        rank = (df_ok.groupby("profile")[["score", "return", "mdd", "trades"]]
                .mean()
                .sort_values("score", ascending=False))
    else:
        rank = pd.DataFrame()

    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_path = out_dir / "batch_profile_eval.csv"
    rk_path = out_dir / "batch_profile_rank.csv"
    df.to_csv(df_path, index=False, encoding="utf-8")
    rank.to_csv(rk_path, encoding="utf-8")

    print(f"[OK] Batch Eval Saved: {df_path}")
    print(f"[OK] Rank Saved: {rk_path}")
    print("\nTop Profiles:")
    print(rank.head(5))


if __name__ == "__main__":
    main()
