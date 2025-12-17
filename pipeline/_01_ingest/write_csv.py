from __future__ import annotations

from pathlib import Path
import os
import pandas as pd

from .normalize_ohlcv import normalize_1m_ohlcv


def _z6(symbol: str) -> str:
    return str(symbol).strip().zfill(6)


def write_minute_csv(symbol: str, df: pd.DataFrame, minute_dir: Path) -> Path:
    """
    표준 출력:
    - {minute_dir}/{symbol}.csv
    - 원자적 저장(temp → replace)
    """
    sym = _z6(symbol)
    minute_dir.mkdir(parents=True, exist_ok=True)

    df_n = normalize_1m_ohlcv(df)

    final_path = minute_dir / f"{sym}.csv"
    tmp_path = minute_dir / f".{sym}.tmp.csv"

    df_n.to_csv(tmp_path, index=False, encoding="utf-8")
    os.replace(tmp_path, final_path)  # atomic replace on Windows
    return final_path
