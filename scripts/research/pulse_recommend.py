# scripts/research/pulse_recommend.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
import yaml

def recommend_max_hold(summary_csv: Path, bucket: int) -> dict:
    """
    규칙:
      A) ev_mean > 0 인 마지막 hold_bucket의 상단
      B) ev_cum_mean 이 0 아래로 내려가기 직전의 hold_bucket 상단
      => 둘 중 작은 값 채택
    """
    df = pd.read_csv(summary_csv)
    df = df.sort_values("hold_bucket")

    # A) EV 양수 마지막
    pos = df[df["ev_mean"] > 0]
    cand_a = int(pos["hold_bucket"].max()) if len(pos) else None

    # B) 누적 EV 평균 0 아래로 내려가기 직전
    below = df[df["ev_cum_mean"] <= 0]
    if len(below):
        first_below_idx = below.index.min()
        prev = df.loc[df.index < first_below_idx]
        cand_b = int(prev["hold_bucket"].max()) if len(prev) else None
    else:
        cand_b = int(df["hold_bucket"].max())

    cands = [c for c in [cand_a, cand_b] if c is not None]
    if not cands:
        return {"recommended": None, "reason": "no_positive_ev"}

    rec = min(cands)

    return {
        "recommended": rec,
        "cand_ev_positive": cand_a,
        "cand_cum_boundary": cand_b,
        "bucket": bucket,
        "reason": "min(ev_positive_last, cum_ev_boundary)"
    }


def write_recommendations(out_yaml: Path, payload: dict):
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)
