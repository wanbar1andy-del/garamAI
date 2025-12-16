# garam_core/schema/fear_schema.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import pandas as pd


class FearSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class FearSchemaSpec:
    timezone: str = "Asia/Seoul"
    allow_na: bool = True  # feature는 일부 결측 허용(정책으로 관리)
    min_score: float = 0.0
    max_score: float = 1.0


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise FearSchemaError(msg)


def validate_fear_df(df: pd.DataFrame, spec: Optional[FearSchemaSpec] = None) -> pd.DataFrame:
    spec = spec or FearSchemaSpec()

    _assert(isinstance(df, pd.DataFrame), "fear_df must be DataFrame.")
    _assert(len(df) > 0, "fear_df is empty.")
    _assert(isinstance(df.index, pd.DatetimeIndex), "fear_df index must be DatetimeIndex.")
    _assert(df.index.tz is not None, "fear_df index must be tz-aware.")
    _assert(df.index.is_monotonic_increasing, "fear_df index must be sorted ascending.")
    _assert("fear_score" in df.columns, "fear_df missing column: fear_score")

    # timezone convertible
    try:
        _ = df.index.tz_convert(spec.timezone)
    except Exception as e:
        raise FearSchemaError(f"fear_df index tz_convert failed: {e}")

    out = df[["fear_score"]].copy()
    out["fear_score"] = pd.to_numeric(out["fear_score"], errors="coerce")

    if not spec.allow_na:
        _assert(out["fear_score"].notna().all(), "fear_score contains NA (not allowed).")

    # range check (ignore NA)
    s = out["fear_score"].dropna()
    _assert(((s >= spec.min_score) & (s <= spec.max_score)).all(), "fear_score out of [0,1] range.")
    return out
