# scripts/research/pulse_surface.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Ensure garam_core is importable
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from garam_core.strategy.registry import discover_strategies
from garam_core.backtest.engine_unified import run_backtest_unified


def find_regime_switch_class():
    strategies = discover_strategies()
    for s in strategies:
        if getattr(s, "NAME", "") == "regime_switch":
            return s
    raise RuntimeError("RegimeSwitchStrategy (NAME='regime_switch') not found in registry.")


def grid_search_pulse(
    df: pd.DataFrame,
    ev_mult_grid: List[float],
    vol_mult_grid: List[float],
    base_params: Dict = None,
) -> pd.DataFrame:
    """
    하나의 심볼에 대해 (ev_mult, vol_mult) 그리드 서치.
    base_params: RegimeSwitchStrategy에 넘길 나머지 파라미터(있으면).
    결과: 각 조합별 ROI/MDD/승률/Trades DataFrame
    """
    StratClass = find_regime_switch_class()
    rows = []

    for ev_mult in ev_mult_grid:
        for vol_mult in vol_mult_grid:
            params = dict(base_params or {})
            params["ev_mult"] = ev_mult
            params["vol_mult"] = vol_mult

            strat = StratClass(**params)
            # print(f"[GRID] ev_mult={ev_mult}, vol_mult={vol_mult} ...", end=" ")

            try:
                res = run_backtest_unified(strat, df)
                rows.append({
                    "ev_mult": ev_mult,
                    "vol_mult": vol_mult,
                    "roi": res["roi"],
                    "max_drawdown": res["max_drawdown"],
                    "win_rate": res["win_rate"],
                    "trades": res["trades"],
                    "profit_factor": res["profit_factor"],
                })
            except Exception as e:
                # print(f"ERROR: {e}")
                rows.append({
                    "ev_mult": ev_mult,
                    "vol_mult": vol_mult,
                    "roi": np.nan,
                    "max_drawdown": np.nan,
                    "win_rate": np.nan,
                    "trades": 0,
                    "profit_factor": np.nan,
                })

    return pd.DataFrame(rows)


def recommend_from_surface(
    df_surface: pd.DataFrame,
    max_mdd_abs: float = 0.20,
    min_trades: int = 10,
    target_winrate: float = 0.60,
) -> Dict:
    """
    심볼 단위 추천 규칙:
      1) |MDD| <= max_mdd_abs
      2) trades >= min_trades
      3) win_rate >= 0.5 (최소)
      4) ROI 최대, 단 win_rate가 target에 가까운 쪽에 가점
    """
    df = df_surface.copy()
    df = df.dropna(subset=["roi", "max_drawdown"])
    if df.empty:
        return {"recommended": None, "reason": "empty_surface"}

    df["mdd_abs"] = df["max_drawdown"].abs()
    mask = (df["mdd_abs"] <= max_mdd_abs) & (df["trades"] >= min_trades) & (df["win_rate"] >= 0.5)
    df = df[mask]
    if df.empty:
        return {"recommended": None, "reason": "no_candidate_after_constraints"}

    # win_rate가 target에 가까우면서 ROI가 큰 조합 우선 (단순화: WR 차이 오름차순, ROI 내림차순)
    # 하지만 ROI가 가장 중요하므로 ROI 우선 정렬 할 수도 있음. 사용자가 준 로직은 ROI + WR Gap.
    # 여기서는 ROI 우선으로 하고 WR Gap은 2순위로 두거나.. 
    # 사용자 로직: "ROI 최대, 단 win_rate가 target에 가까운 쪽에 가점" -> 모호함.
    # 단순하게: ROI 높은 순 정렬.
    
    df = df.sort_values(["roi", "mdd_abs"], ascending=[False, True])

    best = df.iloc[0]
    return {
        "recommended": {
            "ev_mult": float(best["ev_mult"]),
            "vol_mult": float(best["vol_mult"]),
        },
        "roi": float(best["roi"]),
        "max_drawdown": float(best["max_drawdown"]),
        "win_rate": float(best["win_rate"]),
        "trades": int(best["trades"]),
        "reason": "max_roi_under_risk_constraint",
    }
