# garam_core/data/loader.py
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal
import pandas as pd

# [Phase 3-2 Logic Migration]
# Resolve project root to import pipeline
_project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_project_root))
from pipeline.store.data_loader import store as _store_manager


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
    # [Phase 3-2] Redirect 'minute' timeframe to StoreManager (Validated Gate)
    if timeframe == "minute":
        try:
            # store.get_data returns df with 'date' column (datetime due to as_datetime=True default)
            try:
                df = _store_manager.get_data(symbol, as_datetime=True)
            except Exception:
                df = None

            if df is None or df.empty:
                # Fallback to history/minute (Direct File Read)
                # Attempt parquet first, then csv
                hist_dir = data_root / "history" / "minute"
                p_file = hist_dir / f"{symbol}.parquet"
                c_file = hist_dir / f"{symbol}.csv"
                
                if p_file.exists():
                    df = pd.read_parquet(p_file)
                elif c_file.exists():
                    df = pd.read_csv(c_file)
                else:
                    raise DataLoadError(f"Data not found in Store or History for {symbol}")
                
                # Normalize Direct Read
                if "date" not in df.columns and hasattr(df.index, "name") and df.index.name != "date":
                     # If index is date?
                     pass
                     
                # Standardize columns
                df.columns = [c.lower() for c in df.columns]
                if "date" in df.columns:
                     df["date"] = pd.to_datetime(df["date"])
                     
            if df.empty:
                raise DataLoadError(f"Store returned empty data for {symbol}")
                
            # Core loader contract expects DatetimeIndex
            if "date" in df.columns:
                df = df.set_index("date").sort_index()
            
            # Enforce timezone
            if df.index.tz is None:
                df.index = df.index.tz_localize(spec.tz)
            else:
                df.index = df.index.tz_convert(spec.tz)
                
            return df
        except Exception as e:
            raise DataLoadError(f"Load failed for {symbol}: {e}")

    # Legacy fallback for other timeframes (if any) or error
    raise DataLoadError(f"Unsupported timeframe: {timeframe} (Only 'minute' supported via Store)")
