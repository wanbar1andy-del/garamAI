from __future__ import annotations

import pandas as pd


REQUIRED_COLS = ["date", "open", "high", "low", "close", "volume"]


def normalize_1m_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ingest → Validate 계약 최소 충족:
    - date: YYYYMMDDHHMMSS (string)
    - open/high/low/close/volume: int
    - date 정렬, 중복 제거
    """
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"[INGEST-NORM] missing columns: {missing}")

    out = df[REQUIRED_COLS].copy()

    # date normalize
    out["date"] = out["date"].astype(str).str.strip()

    # numeric normalize (강제 int)
    for c in ["open", "high", "low", "close", "volume"]:
        out[c] = pd.to_numeric(out[c], errors="raise").astype("int64")

    # sort + dedup
    out = out.sort_values("date")
    out = out.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    return out
