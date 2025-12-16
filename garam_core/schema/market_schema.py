from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
import pandas as pd


REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class MarketSchemaSpec:
    # timezone 정책: core는 UTC 또는 KST 중 하나로 '고정'해야 합니다.
    # 추천: core는 'UTC'로 고정하고, I/O 레이어에서 KST 변환.
    timezone: str = "UTC"   # "UTC" or "Asia/Seoul"
    allow_na: bool = False
    allow_duplicate_index: bool = False

    # 가격/거래량 기본 제약
    require_positive_prices: bool = True
    require_nonnegative_volume: bool = True

    # OHLC 논리 제약
    enforce_ohlc_logic: bool = True  # high >= max(open, close, low), low <= min(open, close, high)


class SchemaError(ValueError):
    """Raised when market dataframe violates schema contract."""


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise SchemaError(msg)


def validate_market_df(
    df: pd.DataFrame,
    spec: Optional[MarketSchemaSpec] = None,
    required_columns: Iterable[str] = REQUIRED_COLUMNS,
) -> pd.DataFrame:
    """
    Contract:
      - df: index must be DatetimeIndex (tz-aware), sorted ascending
      - required columns: open/high/low/close/volume exist
      - dtypes: numeric coercible (float for prices, int/float for volume)
      - NA: not allowed by default
      - duplicates: not allowed by default
      - OHLC logic enforced by default
    Returns:
      - validated df (copy-safe, columns order normalized)
    """
    spec = spec or MarketSchemaSpec()

    _assert(isinstance(df, pd.DataFrame), "market_df must be a pandas DataFrame.")
    _assert(len(df) > 0, "market_df is empty.")

    # index contract
    # index contract
    # Robust check: explicit class or inferred type
    is_pd_datetime = isinstance(df.index, pd.DatetimeIndex)
    is_inferred = 'datetime' in pd.api.types.infer_dtype(df.index)
    is_datetime = is_pd_datetime or is_inferred
    
    _assert(is_datetime, f"Index must be DatetimeIndex. Got type={type(df.index)} dtype={df.index.dtype}")
    # _assert(df.index.tz is not None, "DatetimeIndex must be timezone-aware (tz-aware).") # Temporarily relaxed for existing data compatibility if needed, but per contract strictness we should enforce or convert.
    # User's code enforces it: `_assert(df.index.tz is not None...)`
    # I will strictly follow the provided code.
    _assert(df.index.tz is not None, "DatetimeIndex must be timezone-aware (tz-aware).")
    
    _assert(df.index.is_monotonic_increasing, "DatetimeIndex must be sorted ascending.")

    if not spec.allow_duplicate_index:
        _assert(~df.index.has_duplicates, "DatetimeIndex contains duplicates (not allowed).")

    # timezone policy
    # NOTE: 'exact tz equality' can be tricky; normalize by converting then checking offset-aware.
    if spec.timezone:
        try:
            _ = df.index.tz_convert(spec.timezone)
        except Exception as e:
            raise SchemaError(f"Index timezone cannot be converted to {spec.timezone}: {e}")

    # columns contract
    for c in required_columns:
        _assert(c in df.columns, f"Missing required column: {c}")

    df2 = df.loc[:, list(required_columns)].copy()

    # dtype coercion
    for c in ("open", "high", "low", "close"):
        df2[c] = pd.to_numeric(df2[c], errors="coerce")
    df2["volume"] = pd.to_numeric(df2["volume"], errors="coerce")

    if not spec.allow_na:
        _assert(df2.notna().all().all(), "NA detected in required columns (not allowed).")

    # basic constraints
    if spec.require_positive_prices:
        _assert((df2[["open", "high", "low", "close"]] > 0).all().all(), "Non-positive price detected.")
    if spec.require_nonnegative_volume:
        _assert((df2["volume"] >= 0).all(), "Negative volume detected.")

    # OHLC logic constraints
    if spec.enforce_ohlc_logic:
        hi = df2["high"]
        lo = df2["low"]
        op = df2["open"]
        cl = df2["close"]

        _assert((hi >= op).all(), "OHLC invalid: high < open exists.")
        _assert((hi >= cl).all(), "OHLC invalid: high < close exists.")
        _assert((hi >= lo).all(), "OHLC invalid: high < low exists.")
        _assert((lo <= op).all(), "OHLC invalid: low > open exists.")
        _assert((lo <= cl).all(), "OHLC invalid: low > close exists.")

    return df2
