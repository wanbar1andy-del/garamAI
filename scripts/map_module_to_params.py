# scripts/map_module_to_params.py
from __future__ import annotations

from pathlib import Path
import yaml
import pandas as pd


def horizon_to_cooldown(h: int) -> int:
    """
    의미 매핑:
    - best_horizon_min ≈ noise decay + 참여자 교체 시간
    """
    if h <= 120:
        return 120
    if h <= 240:
        return 240
    return 360


def mdd_to_fast_exit(mdd: float) -> float:
    """
    mdd_proxy → fast exit drawdown (보수적 상한)
    """
    if pd.isna(mdd):
        return 0.03
    return float(min(0.05, max(0.02, abs(mdd) * 1.2)))


def fear_bucket_to_gate(bucket: str) -> dict:
    """
    공포 분위에 따른 게이트 정책
    """
    if bucket == "HIGH":
        return {"block_entry_above": 0.85, "multiplier_cap": 1.3}
    if bucket == "MID":
        return {"block_entry_above": 0.90, "multiplier_cap": 2.0}
    return {"block_entry_above": 0.95, "multiplier_cap": 2.5}


def main():
    project_root = Path(__file__).resolve().parents[1]
    inp = project_root / "reports" / "modules_discovery.csv"
    if not inp.exists():
        print(f"Discovery report not found: {inp}")
        return

    df = pd.read_csv(inp)

    # 기본 세트 (성공 사례 반영)
    base = {
        "signal": {
            "momentum_n": 120,
            "min_momentum": 0.02,
        },
        "execution": {
            "fill": "NEXT_OPEN",
            "cost": {
                "commission_rate": 0.00015,
                "slippage_rate": 0.00025,
                "sell_tax_rate": 0.00230,
            },
        },
        "risk": {
            "aci_deleverage": {
                "cap_high": 1.3,
                "cap_mid": 2.0,
                "cap_low": 2.5,
            }
        },
        "turbo": {
            "target_vol": 0.02
        }
    }

    sets = {}

    for _, r in df.iterrows():
        cd = horizon_to_cooldown(int(r["best_horizon_min"]))
        fe = mdd_to_fast_exit(float(r["mdd_proxy_best"]))
        gate = fear_bucket_to_gate(str(r["fear_bucket_worst"]))

        params = base.copy()
        params["signal"] = {**params["signal"], "cooldown_bars": cd}
        params["turbo"] = {**params["turbo"], "fast_exit_drawdown": fe}
        params["risk"] = {
            **params["risk"],
            "fear_gate": {
                "enabled": True,
                **gate
            }
        }

        key = f"{r['module']}_v1"
        sets[key] = params

    # Output in format compatible with strategy_profile.yaml "profiles" section
    # keys: profile_name -> config dict
    out_profiles = {}
    for key, val in sets.items():
        out_profiles[key] = {
            "description": f"Generated from module {key.replace('_v1','')} (Alpha Discovery)",
            **val
        }

    out_path = project_root / "reports" / "generated_profiles.yaml"
    out_path.write_text(yaml.safe_dump({"profiles": out_profiles}, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"[OK] Generated profiles saved to: {out_path}")
    print("Action: Copy the content of 'profiles' to 'garam_core/config/strategy_profile.yaml' to use them.")


if __name__ == "__main__":
    main()
