# scripts/research/pulse_recommend_symbolwise.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
import yaml
from scripts.research.pulse_recommend import recommend_max_hold

def recommend_symbolwise(base_dir: Path, bucket: int, top_strategies: list) -> dict:
    """
    base_dir: reports/pulse_hold_ev
    구조: pulse_hold_ev/{symbol}_{strategy}/hold_ev_summary.csv
    
    Returns:
      {
        "005930": { "recommended": 10, ... },
        "000660": { "recommended": 5, ... }
      }
    """
    rec_map = {}

    if not base_dir.exists():
        return rec_map

    for symbol_strategy_dir in base_dir.glob("*"):
        if not symbol_strategy_dir.is_dir():
            continue

        name = symbol_strategy_dir.name  # "005930_mean_reversion" 형식
        if "_" not in name:
            continue

        # 전략명 매칭 (단순화: 뒤에서부터 strategy 찾기 or split)
        # 보통 "{symbol}_{strategy}" 형태. strategy에 _가 있을 수 있으니 주의.
        # 여기서는 "known strategies" 리스트를 이용해 매칭
        
        found_strat = None
        target_sym = None
        
        for strat in top_strategies:
            if name.endswith(f"_{strat}"):
                found_strat = strat
                # symbol은 나머지 앞부분
                target_sym = name[:-len(strat)-1]
                break
        
        if not found_strat:
            continue

        summary_csv = symbol_strategy_dir / "hold_ev_summary.csv"
        if not summary_csv.exists():
            continue

        rec = recommend_max_hold(summary_csv, bucket=bucket)
        if rec.get("recommended"):
            rec_map[target_sym] = rec

    return rec_map


def write_symbolwise_recommendations(out_yaml: Path, payload: dict):
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)
