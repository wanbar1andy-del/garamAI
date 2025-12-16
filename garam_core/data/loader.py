# garam_core/data/loader.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal
import pandas as pd


class DataLoadError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoadSpec:
    """
    Core loader contract:
      - I/O only here.
      - Index must be datetime; tz-aware conversion is enforced.
    """
    tz: str = "UTC"  # core timezone
    file_type: Optional[Literal["csv", "parquet"]] = None  # autodetect if None


def _infer_file_type(p: Path) -> str:
    suf = p.suffix.lower().lstrip(".")
    if suf in ("csv", "parquet"):
        return suf
    raise DataLoadError(f"Unsupported file type: {p.name}")


def load_ohlcv(
    data_root: Path,
    symbol: str,
    timeframe: str,
    spec: LoadSpec = LoadSpec(),
) -> pd.DataFrame:
    """
    Load OHLCV from data_root using a deterministic convention.

    Convention (you can adapt, but MUST be consistent):
      data_root/
        history/
          {timeframe}/
            {symbol}.csv  OR  {symbol}.parquet

    Required columns (raw): open, high, low, close, volume
    Required index: datetime in column 'date' or index itself (loader will normalize).

    Returns raw df (schema validation happens in Gate1, not here).
    """
    # 후보 경로: parquet 우선 -> csv
    base_dir = (data_root / "history" / timeframe).resolve()
    if not base_dir.exists():
        raise DataLoadError(f"History dir not found: {base_dir}")

    # autodetect
    p_parq = base_dir / f"{symbol}.parquet"
    p_csv = base_dir / f"{symbol}.csv"

    if spec.file_type == "parquet" or (spec.file_type is None and p_parq.exists()):
        path = p_parq if p_parq.exists() else None
        if path is None:
            raise DataLoadError(f"Parquet not found: {p_parq}")
        df = pd.read_parquet(path)
    else:
        path = p_csv if p_csv.exists() else None
        if path is None:
            raise DataLoadError(f"CSV not found: {p_csv}")
        df = pd.read_csv(path)

    if not isinstance(df, pd.DataFrame) or len(df) == 0:
        raise DataLoadError(f"Loaded empty dataframe: {path}")

    # normalize datetime index
    if "date" in df.columns:
        # data often comes as Int64 (YYYYMMDDHHMMSS). Direct to_datetime treats as nanos (1970).
        # Force string conversion first to allow smart parsing.
        df["date"] = pd.to_datetime(df["date"].astype(str), errors="raise")
        df = df.set_index("date")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise DataLoadError("Loaded data has no DatetimeIndex (missing 'date' column?).")

    # enforce tz-aware index
    if df.index.tz is None:
        # treat as naive -> localize to spec.tz (strict, deterministic policy)
        df.index = df.index.tz_localize(spec.tz)
    else:
        df.index = df.index.tz_convert(spec.tz)

    df = df.sort_index()
    return df
