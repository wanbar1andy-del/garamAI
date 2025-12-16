# garam_core/data/feature_loader.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import pandas as pd

from garam_core.schema.fear_schema import validate_fear_df, FearSchemaSpec, FearSchemaError


class FeatureLoadError(RuntimeError):
    pass


@dataclass(frozen=True)
class FeatureLoadSpec:
    tz: str = "Asia/Seoul"


def load_fear_feature(
    data_root: Path,
    timeframe: str = "minute",
    symbol: str = "MARKET",
    spec: FeatureLoadSpec = FeatureLoadSpec(),
) -> pd.DataFrame:
    """
    Expected:
      data_root/features/fear/{timeframe}/{symbol}.parquet
    """
    path = (data_root / "features" / "fear" / timeframe / f"{symbol}.parquet").resolve()
    if not path.exists():
        raise FeatureLoadError(f"Fear feature not found: {path}")

    df = pd.read_parquet(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="raise")
        df = df.set_index("date")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise FeatureLoadError("Fear feature has no DatetimeIndex (missing 'date'?).")

    # tz normalize
    if df.index.tz is None:
        df.index = df.index.tz_localize(spec.tz)
    else:
        df.index = df.index.tz_convert(spec.tz)

    df = df.sort_index()

    # schema validate
    try:
        return validate_fear_df(df, FearSchemaSpec(timezone=spec.tz))
    except FearSchemaError as e:
        raise FeatureLoadError(f"Fear schema failed: {e}")


def align_fear_to_market(
    market_df: pd.DataFrame,
    fear_df: pd.DataFrame,
    fallback_score: float = 0.5,
) -> pd.DataFrame:
    """
    Left-join fear onto market index, forward-fill, then fallback.
    Returns a DataFrame with 'fear_score' aligned to market_df index.
    """
    aligned = fear_df.reindex(market_df.index, method="ffill")
    aligned["fear_score"] = aligned["fear_score"].fillna(float(fallback_score))
    return aligned[["fear_score"]]
