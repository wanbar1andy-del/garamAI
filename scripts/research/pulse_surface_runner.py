# scripts/research/pulse_surface_runner.py
from __future__ import annotations
from pathlib import Path
import yaml
from typing import Dict, List

import pandas as pd

from scripts.research.pulse_surface import grid_search_pulse, recommend_from_surface


def run_surface_for_symbols(
    dfs: Dict[str, pd.DataFrame],
    ev_mult_grid: List[float],
    vol_mult_grid: List[float],
    base_params: Dict,
    max_mdd_abs: float,
    min_trades: int,
    target_winrate: float,
    out_dir: Path,
) -> Dict[str, Dict]:
    """
    dfs: {symbol: df}
    반환: {symbol: {recommended:{ev_mult,vol_mult},...}}
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    rec_map: Dict[str, Dict] = {}

    for sym, df in dfs.items():
        print(f"\n[PULSE SURFACE] Symbol={sym}")
        surface = grid_search_pulse(
            df=df,
            ev_mult_grid=ev_mult_grid,
            vol_mult_grid=vol_mult_grid,
            base_params=base_params,
        )
        surface_path = out_dir / f"surface_{sym}.csv"
        surface.to_csv(surface_path, index=False, encoding="utf-8-sig")

        rec = recommend_from_surface(
            surface,
            max_mdd_abs=max_mdd_abs,
            min_trades=min_trades,
            target_winrate=target_winrate,
        )
        rec_map[sym] = rec

        if rec.get("recommended"):
            print(f"  => RECOMMEND: {rec['recommended']} (ROI {rec['roi']:.2%})")
        else:
            print(f"  => NO RECOMMENDATION: {rec.get('reason')}")

    return rec_map


def save_surface_recommendations(path: Path, rec_map: Dict[str, Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(rec_map, f, allow_unicode=True, sort_keys=False)
