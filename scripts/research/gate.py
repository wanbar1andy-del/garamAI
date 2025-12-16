# scripts/research/gate.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Optional
import json
import pandas as pd

@dataclass
class GateConfig:
    # ROI 우선(요청 반영): ROI가 개선되면 채택
    # 단, MDD 한도는 생존 조건(예: 20%)
    max_mdd_abs: float = 0.20           # |MDD| <= 20%
    min_trades: int = 5                # 너무 적은 거래는 의미 없음
    improve_roi_min: float = 0.0       # ROI가 이전 대비 최소 얼마나 개선되어야 채택? 0이면 '개선되면 채택'

def load_summary_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"summary.csv not found: {path}")
    df = pd.read_csv(path)
    # 필수 컬럼 최소 체크
    need = {"symbol","strategy","roi","max_drawdown","trades","win_rate"}
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"summary.csv missing columns: {miss}")
    return df

def aggregate_portfolio_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    전략별로 (심볼 평균 ROI, 심볼 평균 MDD, 총 trades, 평균 win_rate) 계산
    """
    agg = (
        df.groupby("strategy", as_index=False)
          .agg(
              roi_mean=("roi","mean"),
              mdd_mean=("max_drawdown","mean"),
              trades_sum=("trades", "sum"),
              win_rate_mean=("win_rate","mean"),
              profit_factor_mean=("profit_factor","mean") if "profit_factor" in df.columns else ("roi","mean"),
          )
    )
    return agg

def decide_accept(
    prev_summary: Optional[pd.DataFrame],
    curr_summary: pd.DataFrame,
    cfg: GateConfig
) -> Tuple[bool, str]:
    """
    채택 규칙(간결):
    - 생존 조건: 전략별로 (|MDD_mean| <= max_mdd_abs) AND (trades_sum >= min_trades)
    - ROI 우선: 이전 대비 roi_mean이 개선된 전략이 있으면 채택(기본 0.0 이상 개선)
    - 이전이 없으면: 생존 조건 통과하는 best roi 전략이 있으면 채택
    """
    curr = aggregate_portfolio_score(curr_summary)
    # 생존 필터
    curr["mdd_abs"] = curr["mdd_mean"].abs()
    surv = curr[(curr["mdd_abs"] <= cfg.max_mdd_abs) & (curr["trades_sum"] >= cfg.min_trades)].copy()

    if surv.empty:
        return False, f"GATE FAIL: survivable strategy 없음 (|MDD|<={cfg.max_mdd_abs}, trades>={cfg.min_trades})"

    # 현재 best
    curr_best = surv.sort_values(["roi_mean","mdd_abs"], ascending=[False, True]).head(1).iloc[0]
    curr_best_name = curr_best["strategy"]
    curr_best_roi = float(curr_best["roi_mean"])
    curr_best_mdd = float(curr_best["mdd_mean"])
    curr_best_tr = int(curr_best["trades_sum"])

    if prev_summary is None:
        return True, f"GATE PASS (first run): best={curr_best_name}, roi={curr_best_roi:.4f}, mdd={curr_best_mdd:.4f}, trades={curr_best_tr}"

    prev = aggregate_portfolio_score(prev_summary)
    prev_map = {row["strategy"]: row for _, row in prev.iterrows()}

    if curr_best_name not in prev_map:
        # 새 전략이 추가되어 등장한 경우: 생존 통과면 채택
        return True, f"GATE PASS (new best strategy): best={curr_best_name}, roi={curr_best_roi:.4f}, mdd={curr_best_mdd:.4f}, trades={curr_best_tr}"

    prev_best_roi = float(prev_map[curr_best_name]["roi_mean"])
    improve = curr_best_roi - prev_best_roi

    if improve >= cfg.improve_roi_min:
        return True, f"GATE PASS: best={curr_best_name}, roi 개선 {prev_best_roi:.4f}->{curr_best_roi:.4f} (Δ={improve:.4f}), mdd={curr_best_mdd:.4f}, trades={curr_best_tr}"

    return False, f"GATE FAIL: best={curr_best_name}, roi 개선 부족 {prev_best_roi:.4f}->{curr_best_roi:.4f} (Δ={improve:.4f}), mdd={curr_best_mdd:.4f}, trades={curr_best_tr}"

def write_manifest(out_dir: Path, manifest: dict) -> Path:
    p = out_dir / "run_manifest.json"
    p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
