from __future__ import annotations

from typing import Iterable, Any
from datetime import datetime
import pandas as pd
import numpy as np

OHLCV_RENAME = {
    "체결시간": "date",
    "datetime": "date",
    "현재가": "close",
    "종가": "close",
    "시가": "open",
    "고가": "high",
    "저가": "low",
    "거래량": "volume",
}

def normalize_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c: OHLCV_RENAME[c] for c in df.columns if c in OHLCV_RENAME}
    if cols:
        df = df.rename(columns=cols)
    return df

def ensure_cols(df: pd.DataFrame, required: Iterable[str]) -> bool:
    return all(c in df.columns for c in required)

def parse_minute_ts_to_date(s: pd.Series) -> pd.Series:
    # YYYYMMDDHHMMSS -> YYYYMMDD
    return s.astype(str).str.slice(0, 8)

def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default

def safe_int(x: Any, default: int = 0) -> int:
    try:
        if pd.isna(x):
            return default
        return int(float(x))
    except Exception:
        return default

def rsi_wilder(close: pd.Series, window: int) -> pd.Series:
    """
    Wilder RSI series via EWM (alpha=1/window).
    Safety:
      - avg_loss==0 => RSI=100
      - avg_gain==0 and avg_loss==0 => RSI=50
    """
    close = pd.to_numeric(close, errors="coerce")
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    avg_gain = gain.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False, min_periods=window).mean()

    rsi = pd.Series(np.nan, index=close.index, dtype="float64")
    both_zero = (avg_gain == 0) & (avg_loss == 0)
    loss_zero = (avg_loss == 0) & (~both_zero)

    rsi[both_zero] = 50.0
    rsi[loss_zero] = 100.0

    ok = ~(both_zero | loss_zero)
    rs = avg_gain[ok] / avg_loss[ok].replace(0, np.nan)
    rsi[ok] = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def true_range(high: pd.Series, low: pd.Series, prev_close: pd.Series) -> pd.Series:
    high = pd.to_numeric(high, errors="coerce")
    low = pd.to_numeric(low, errors="coerce")
    prev_close = pd.to_numeric(prev_close, errors="coerce")
    tr1 = (high - low).abs()
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = true_range(high, low, prev_close)
    return tr.rolling(window, min_periods=window).mean()

def zscore(series: pd.Series, window: int) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    m = s.rolling(window, min_periods=window).mean()
    sd = s.rolling(window, min_periods=window).std(ddof=0)
    return (s - m) / sd.replace(0, np.nan)

def pct_return(series: pd.Series, periods: int) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    return s.pct_change(periods=periods)

def ew_universe_return(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Equal-weight universe daily return from daily close.
    Input columns: date, symbol, close
    Output columns: date, mkt_ret_1
    """
    d = df_daily.copy()
    d["close"] = pd.to_numeric(d["close"], errors="coerce")
    d = d.sort_values(["symbol", "date"])
    d["ret_1"] = d.groupby("symbol")["close"].pct_change(1)
    m = d.groupby("date")["ret_1"].mean().reset_index().rename(columns={"ret_1": "mkt_ret_1"})
    return m
