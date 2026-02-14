from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

from scripts._hero_common import normalize_ohlcv_columns, parse_minute_ts_to_date, now_ts, ensure_cols

REQUIRED_MINUTE_COLS = ["date", "open", "high", "low", "close", "volume"]

def read_universe(universe_path: Path) -> list[str]:
    df = pd.read_csv(universe_path)
    col = None
    for c in ["Code", "code", "symbol", "Symbol", "ticker", "Ticker"]:
        if c in df.columns:
            col = c
            break
    if col is None:
        raise ValueError(f"Universe CSV has no recognizable symbol column. cols={list(df.columns)}")
    syms = df[col].astype(str).str.strip().str.zfill(6).tolist()
    syms = [s for s in syms if s.isdigit() and len(s) == 6]
    return sorted(set(syms))

def build_daily_for_symbol(minute_csv: Path, lookback_days: int) -> pd.DataFrame:
    if not minute_csv.exists():
        return pd.DataFrame()

    chunksize = 200_000
    dates_seen: set[str] = set()
    parts: list[pd.DataFrame] = []

    reader = pd.read_csv(minute_csv, chunksize=chunksize, dtype={"date": "string"})
    for chunk in reader:
        chunk = normalize_ohlcv_columns(chunk)
        if not ensure_cols(chunk, REQUIRED_MINUTE_COLS):
            if "체결시간" in chunk.columns:
                chunk = chunk.rename(columns={"체결시간": "date"})
            if not ensure_cols(chunk, REQUIRED_MINUTE_COLS):
                return pd.DataFrame()

        chunk["date"] = chunk["date"].astype(str)
        chunk["d"] = parse_minute_ts_to_date(chunk["date"])
        chunk = chunk[["d", "date", "open", "high", "low", "close", "volume"]].copy()

        parts.append(chunk)
        dates_seen.update(chunk["d"].unique().tolist())
        if len(dates_seen) >= lookback_days + 20:
            break

    if not parts:
        return pd.DataFrame()

    df = pd.concat(parts, ignore_index=True)
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["date", "close"])
    df = df.sort_values("date", ascending=True)

    g = df.groupby("d", sort=True)
    daily = pd.DataFrame({
        "date": g["d"].first(),
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "volume": g["volume"].sum(),
    }).reset_index(drop=True)

    daily = daily.sort_values("date", ascending=True).tail(lookback_days).reset_index(drop=True)
    return daily

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".", help="Project root (contains GARAM_Data)")
    p.add_argument("--lookback_days", type=int, default=365)
    p.add_argument("--universe_csv", default="GARAM_Data/real_universe_400.csv")
    p.add_argument("--minute_dir", default="GARAM_Data/history/minute")
    p.add_argument("--out", default="datasets/daily/daily_1y.csv")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    universe_path = project_root / args.universe_csv
    minute_dir = project_root / args.minute_dir
    out_path = project_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    symbols = read_universe(universe_path)
    if args.limit:
        symbols = symbols[:args.limit]

    rows = []
    bad = 0
    for sym in symbols:
        minute_csv = minute_dir / f"{sym}.csv"
        d = build_daily_for_symbol(minute_csv, lookback_days=int(args.lookback_days))
        if d.empty:
            bad += 1
            continue
        d.insert(1, "symbol", sym)
        rows.append(d)

    if not rows:
        raise SystemExit("[FAIL] No daily rows created. Check minute_dir and schemas.")

    df_out = pd.concat(rows, ignore_index=True)
    df_out["date"] = df_out["date"].astype(str)
    df_out["symbol"] = df_out["symbol"].astype(str).str.zfill(6)

    df_out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] daily snapshot written: {out_path}")
    print(f"- symbols={len(symbols)} ok={df_out['symbol'].nunique()} bad={bad}")
    print(f"- rows={len(df_out)} dates={df_out['date'].nunique()} ts={now_ts()}")

if __name__ == "__main__":
    main()
