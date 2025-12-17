from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import pandas as pd


REQUIRED_COLS = ["date", "open", "high", "low", "close", "volume"]
DATE_RE = re.compile(r"^\d{14}$")  # YYYYMMDDHHMMSS


@dataclass
class ValidateResult:
    symbol: str
    status: str  # OK / WARN / FAIL
    in_rows: int
    out_rows: int
    dups_removed: int
    outliers: int
    date_min: str | None
    date_max: str | None
    message: str


def _z6(symbol: str) -> str:
    return str(symbol).strip().zfill(6)


def _atomic_write_csv(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(f".{out_path.name}.tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, out_path)


def validate_and_tag_minute_df(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    # 1) 스키마
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"[VALIDATE] missing columns: {missing}")

    out = df[REQUIRED_COLS].copy()

    # 2) 타입/포맷
    out["date"] = out["date"].astype(str).str.strip()
    bad_date = ~out["date"].str.match(DATE_RE)
    if bad_date.any():
        out = out.loc[~bad_date].copy()

    for c in ["open", "high", "low", "close", "volume"]:
        out[c] = pd.to_numeric(out[c], errors="raise").astype("int64")

    # 3) 정렬/중복
    in_rows = len(out)
    out = out.sort_values("date").reset_index(drop=True)
    before = len(out)
    out = out.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    dups_removed = before - len(out)

    # 4) 기본 무결성
    bad_ohlc = (out["high"] < out[["open", "close"]].max(axis=1)) | (out["low"] > out[["open", "close"]].min(axis=1))
    bad_nonpos = (out[["open", "high", "low", "close", "volume"]] <= 0).any(axis=1)

    # 5) Outlier 태깅(MVP)
    ret = out["close"].pct_change().fillna(0.0)
    outlier_ret = ret.abs() >= 0.15
    is_outlier = outlier_ret | bad_ohlc | bad_nonpos

    out["is_outlier"] = is_outlier.astype(bool)

    # 6) 결측치 보간 태그(MVP: fill은 아직 안 함)
    out["is_filled"] = False

    meta = {
        "in_rows": in_rows,
        "out_rows": len(out),
        "dups_removed": int(dups_removed),
        "outliers": int(out["is_outlier"].sum()),
        "date_min": out["date"].iloc[0] if len(out) else None,
        "date_max": out["date"].iloc[-1] if len(out) else None,
    }
    return out, meta


def validate_minute_csv(symbol: str, in_path: Path, out_path: Path | None = None) -> tuple[Path, ValidateResult]:
    sym = _z6(symbol)
    df = pd.read_csv(in_path)

    cleaned, meta = validate_and_tag_minute_df(df)

    # 기본 출력: {data_root}/validated/minute/{symbol}.csv
    out_path = out_path or (in_path.parent.parent.parent / "validated" / "minute" / f"{sym}.csv")
    _atomic_write_csv(cleaned, out_path)

    status = "OK"
    msg = "validated"
    if meta["out_rows"] == 0:
        status = "FAIL"
        msg = "empty after validation"
    elif meta["outliers"] > 0 or meta["dups_removed"] > 0:
        status = "WARN"
        msg = f"outliers={meta['outliers']} dups_removed={meta['dups_removed']}"

    res = ValidateResult(
        symbol=sym,
        status=status,
        in_rows=int(meta["in_rows"]),
        out_rows=int(meta["out_rows"]),
        dups_removed=int(meta["dups_removed"]),
        outliers=int(meta["outliers"]),
        date_min=meta["date_min"],
        date_max=meta["date_max"],
        message=msg,
    )
    return out_path, res
