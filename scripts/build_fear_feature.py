# scripts/build_fear_feature.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import yaml


def keyword_score(text: str, kws_high: List[str], kws_mid: List[str]) -> float:
    t = (text or "").lower()
    s = 0.0
    for k in kws_high:
        if k.lower() in t:
            s += 1.0
    for k in kws_mid:
        if k.lower() in t:
            s += 0.4
    return s


def normalize_score(x: float) -> float:
    # 간단한 포화함수: 0~1
    # 0 -> 0.0, 1 -> ~0.5, 2 -> ~0.75, 3 -> ~0.88 ...
    return float(1.0 - (0.5 ** max(0.0, x)))


def main():
    project_root = Path(__file__).resolve().parents[1]
    cfg_path = project_root / "garam_core" / "config" / "rss_sources.yaml"
    data_root = (project_root / "GARAM_Data").resolve()  # 필요 시 paths.yaml에 맞춤

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    kws = cfg.get("keywords", {})
    kws_high = kws.get("high", [])
    kws_mid = kws.get("mid", [])

    raw_dir = data_root / "raw" / "news" / "rss"
    files = sorted(raw_dir.glob("rss_*.jsonl"))
    if not files:
        # No raw files? Exit gracefully (maybe first run)
        # But user might want to know.
        print(f"No raw rss jsonl found in {raw_dir}")
        return

    rows = []
    for fp in files:
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if "title" not in obj:
                continue

            published = obj.get("published_at", "")
            ts = pd.to_datetime(published, errors="coerce")
            if pd.isna(ts):
                continue
            if ts.tzinfo is None:
                ts = ts.tz_localize("Asia/Seoul")
            else:
                ts = ts.tz_convert("Asia/Seoul")

            text = (obj.get("title", "") + " " + obj.get("description", "")).strip()
            raw_s = keyword_score(text, kws_high, kws_mid)
            score = normalize_score(raw_s)

            rows.append({
                "ts": ts.floor("min"),
                "fear_score_raw": raw_s,
                "fear_score": score,
                "provider": obj.get("provider", ""),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        print("No valid rss rows parsed; fear feature cannot be built.")
        return

    # 분 단위 집계: 평균 fear_score, 기사 수
    g = df.groupby("ts").agg(
        fear_score=("fear_score", "mean"),
        source_count=("provider", "count"),
    ).sort_index()

    # 0~1 clamp
    g["fear_score"] = g["fear_score"].clip(0.0, 1.0)

    out_dir = data_root / "features" / "fear" / "minute"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "MARKET.parquet"
    g.to_parquet(out_path)

    print(f"[OK] Fear feature built: {out_path}")
    print(f"rows={len(g)}, from_raw_files={len(files)}")


if __name__ == "__main__":
    main()
