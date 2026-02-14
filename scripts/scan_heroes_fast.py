from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Any

import pandas as pd


# -------------------------
# IO / Atomic helpers
# -------------------------
def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _read_universe(universe_path: Path) -> list[str]:
    df = pd.read_csv(universe_path)

    # Common columns: Code / code / symbol
    col = None
    for c in ["Code", "code", "symbol", "Symbol", "ticker", "Ticker"]:
        if c in df.columns:
            col = c
            break
    if col is None:
        raise ValueError(f"Universe CSV has no recognizable symbol column. cols={list(df.columns)}")

    syms = df[col].astype(str).str.strip().str.zfill(6).tolist()
    # Keep only 6-digit numeric
    syms = [s for s in syms if s.isdigit() and len(s) == 6]
    # stable unique
    return sorted(set(syms))


def _normalize_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "체결시간": "date",
        "datetime": "date",
        "현재가": "close",
        "종가": "close",
        "시가": "open",
        "고가": "high",
        "저가": "low",
        "거래량": "volume",
    }
    cols = {c: rename_map[c] for c in df.columns if c in rename_map}
    if cols:
        df = df.rename(columns=cols)
    return df


# -------------------------
# Indicator / Probe
# -------------------------
def rsi_wilder(close: pd.Series, window: int) -> float:
    """
    Wilder RSI via EWM (alpha=1/window), common in trading implementations.
    Returns latest RSI (float) or NaN.
    """
    close = pd.to_numeric(close, errors="coerce")
    close = close.dropna()
    if len(close) < window + 2:
        return float("nan")

    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()

    # [FIX] avg_loss == 0 -> RSI=100, avg_gain == 0 -> RSI=0
    last_ag = avg_gain.iloc[-1]
    last_al = avg_loss.iloc[-1]
    try:
        if float(last_al) == 0.0:
            return 100.0 if float(last_ag) > 0.0 else 0.0
    except Exception:
        pass

    rs = avg_gain / avg_loss.replace(0.0, 1e-12)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    try:
        return float(rsi.iloc[-1])
    except Exception:
        return float("nan")


def compute_probe(probe: str, df: pd.DataFrame, window: int) -> dict[str, Any]:
    """
    Compute (close, rsi, score, is_hero) for a given probe.
    Currently supports MR_RSI_30.
    """
    if "close" not in df.columns or "date" not in df.columns:
        return {
            "status": "bad_schema",
            "close": None,
            "rsi": None,
            "score": 0.0,
            "is_hero": 0,
        }

    # Ensure chronological order for RSI
    # date is string like YYYYMMDDHHMMSS
    df = df.copy()
    df["date"] = df["date"].astype(str)
    df = df.sort_values("date", ascending=True)

    close = pd.to_numeric(df["close"], errors="coerce").dropna()
    if close.empty:
        return {"status": "no_close", "close": None, "rsi": None, "score": 0.0, "is_hero": 0}

    last_close = float(close.iloc[-1])

    if probe.upper() == "MR_RSI_30":
        rsi_val = rsi_wilder(close, window)
        if pd.isna(rsi_val):
            return {"status": "insufficient", "close": last_close, "rsi": None, "score": 0.0, "is_hero": 0}

        thr = 30.0
        score = max(0.0, (thr - float(rsi_val)) / thr)
        is_hero = 1 if float(rsi_val) <= thr else 0
        return {"status": "ok", "close": last_close, "rsi": float(rsi_val), "score": float(score), "is_hero": is_hero}

    raise ValueError(f"Unsupported probe: {probe}")


# -------------------------
# Cache
# -------------------------
def cache_path(cache_dir: Path, probe: str, window: int, tail_rows: int, symbol: str) -> Path:
    return cache_dir / probe / f"w{window}" / f"tail{tail_rows}" / f"{symbol}.json"


def load_cache(path: Path, mtime_ns: int, size: int) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if int(d.get("mtime_ns", -1)) != int(mtime_ns):
            return None
        if int(d.get("size", -1)) != int(size):
            return None
        return d
    except Exception:
        return None


def save_cache(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


# -------------------------
# Core scan
# -------------------------
def scan_heroes_fast(
    project_root: Path,
    probe: str,
    window: int,
    limit: int | None,
    tail_rows: int,
    two_pass: bool,
    top_k: int,
    tail_rows2: int | None,
    allocate: bool,
    aum: float,
    alloc_mode: str,
    fast_cache: bool,
    cache_dir: Path,
    write_outputs: bool,
) -> dict[str, Any]:
    t0 = time.time()

    universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
    minute_dir = project_root / "GARAM_Data" / "history" / "minute"
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    symbols = _read_universe(universe_path)
    if limit:
        symbols = symbols[:limit]

    rows_out: list[dict[str, Any]] = []
    cache_hit = 0
    cache_miss = 0
    err = 0

    def process_one(sym: str, nrows: int) -> dict[str, Any]:
        nonlocal cache_hit, cache_miss, err
        csv_path = minute_dir / f"{sym}.csv"
        if not csv_path.exists():
            err += 1
            return {
                "symbol": sym,
                "status": "missing_csv",
                "last_date": None,
                "close": None,
                "rsi": None,
                "score": 0.0,
                "is_hero": 0,
                "cache_hit": 0,
                "read_rows": 0,
                "elapsed_ms": 0,
            }

        st = csv_path.stat()
        mtime_ns = int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9)))
        size = int(st.st_size)

        cpath = cache_path(cache_dir, probe, window, nrows, sym)
        if fast_cache:
            cd = load_cache(cpath, mtime_ns, size)
            if cd is not None:
                cache_hit += 1
                return {
                    "symbol": sym,
                    "status": cd.get("status", "ok"),
                    "last_date": cd.get("last_date"),
                    "close": cd.get("close"),
                    "rsi": cd.get("rsi"),
                    "score": cd.get("score", 0.0),
                    "is_hero": cd.get("is_hero", 0),
                    "cache_hit": 1,
                    "read_rows": cd.get("read_rows", 0),
                    "elapsed_ms": 0,
                }

        cache_miss += 1
        t1 = time.time()
        try:
            df = pd.read_csv(csv_path, nrows=nrows, dtype={"date": "string"})
            df = _normalize_ohlcv_columns(df)
            
            # [FIX] Validate sort order (newest-first required for tail_rows)
            if "date" in df.columns:
                s = df["date"].astype(str)
                if len(s) >= 2 and s.iloc[0] < s.iloc[1]:
                    # Ascending order (old data first) - WRONG for tail_rows!
                    return {
                        "symbol": sym,
                        "status": "bad_order_asc",
                        "last_date": str(s.max()),
                        "close": None,
                        "rsi": None,
                        "score": 0.0,
                        "is_hero": 0,
                        "cache_hit": 0,
                        "read_rows": int(min(len(df), nrows)),
                        "elapsed_ms": int((time.time() - t1) * 1000),
                    }
        except Exception:
            err += 1
            return {
                "symbol": sym,
                "status": "read_error",
                "last_date": None,
                "close": None,
                "rsi": None,
                "score": 0.0,
                "is_hero": 0,
                "cache_hit": 0,
                "read_rows": 0,
                "elapsed_ms": int((time.time() - t1) * 1000),
            }

        if df.empty:
            err += 1
            return {
                "symbol": sym,
                "status": "empty_csv",
                "last_date": None,
                "close": None,
                "rsi": None,
                "score": 0.0,
                "is_hero": 0,
                "cache_hit": 0,
                "read_rows": 0,
                "elapsed_ms": int((time.time() - t1) * 1000),
            }

        last_date = None
        if "date" in df.columns:
            try:
                last_date = str(df["date"].astype(str).max())
            except Exception:
                last_date = None

        out = compute_probe(probe, df, window)
        elapsed_ms = int((time.time() - t1) * 1000)

        row = {
            "symbol": sym,
            "status": out.get("status"),
            "last_date": last_date,
            "close": out.get("close"),
            "rsi": out.get("rsi"),
            "score": float(out.get("score", 0.0) or 0.0),
            "is_hero": int(out.get("is_hero", 0) or 0),
            "cache_hit": 0,
            "read_rows": int(min(len(df), nrows)),
            "elapsed_ms": elapsed_ms,
        }

        if fast_cache:
            payload = {
                "symbol": sym,
                "probe": probe,
                "window": window,
                "tail_rows": nrows,
                "csv_path": str(csv_path),
                "mtime_ns": mtime_ns,
                "size": size,
                "last_date": last_date,
                "status": row["status"],
                "close": row["close"],
                "rsi": row["rsi"],
                "score": row["score"],
                "is_hero": row["is_hero"],
                "read_rows": row["read_rows"],
            }
            save_cache(cpath, payload)

        return row

    # Pass 1
    for sym in symbols:
        rows_out.append(process_one(sym, tail_rows))

    df_out = pd.DataFrame(rows_out)
    df_out["score"] = pd.to_numeric(df_out["score"], errors="coerce").fillna(0.0)

    # Optional Pass 2 (refine top_k)
    if two_pass:
        tr2 = tail_rows2 if tail_rows2 is not None else min(int(tail_rows * 3), 200000)
        top = df_out.sort_values("score", ascending=False).head(int(top_k))
        top_syms = top["symbol"].astype(str).tolist()

        refined = []
        for sym in top_syms:
            refined.append(process_one(sym, tr2))
        df_ref = pd.DataFrame(refined).set_index("symbol")

        # merge refined rows back
        df_out = df_out.set_index("symbol")
        for c in ["status", "last_date", "close", "rsi", "score", "is_hero", "cache_hit", "read_rows", "elapsed_ms"]:
            if c in df_ref.columns:
                df_out.loc[df_ref.index, c] = df_ref[c]
        df_out = df_out.reset_index()

    # Outputs
    ts = _now_ts()
    hero_scan_path = results_dir / f"hero_scan_{probe}_{ts}.csv"

    if write_outputs:
        df_out.to_csv(hero_scan_path, index=False, encoding="utf-8-sig")

    allocation_path = None
    if allocate:
        heroes = df_out[(df_out["is_hero"] == 1) & (df_out["score"] > 0)].copy()
        if heroes.empty:
            alloc = pd.DataFrame(columns=["symbol", "weight", "capital_alloc", "qty", "close", "score", "strategy"])
        else:
            if alloc_mode == "equal":
                heroes["weight"] = 1.0 / len(heroes)
            else:  # score
                s = heroes["score"].sum()
                heroes["weight"] = heroes["score"] / s if s > 0 else (1.0 / len(heroes))
            heroes["capital_alloc"] = heroes["weight"] * float(aum)
            heroes["close"] = pd.to_numeric(heroes["close"], errors="coerce").fillna(0.0)
            
            # [FIX] Protect against close=0 (division by zero -> qty explosion)
            heroes["qty"] = 0  # Default
            heroes.loc[heroes["close"] <= 0, "qty"] = 0
            mask = heroes["close"] > 0
            heroes.loc[mask, "qty"] = (heroes.loc[mask, "capital_alloc"] / heroes.loc[mask, "close"])
            heroes["qty"] = heroes["qty"].fillna(0.0).astype(float)
            heroes["qty"] = heroes["qty"].apply(lambda x: int(x) if x > 0 else 0)
            
            heroes["strategy"] = probe
            alloc = heroes[["symbol", "weight", "capital_alloc", "qty", "close", "score", "strategy"]].copy()

        allocation_path = results_dir / f"allocation_{probe}_{ts}.csv"
        if write_outputs:
            alloc.to_csv(allocation_path, index=False, encoding="utf-8-sig")

    elapsed = time.time() - t0
    return {
        "hero_scan_path": str(hero_scan_path) if write_outputs else None,
        "allocation_path": str(allocation_path) if (write_outputs and allocation_path) else None,
        "rows": len(df_out),
        "heroes": int((df_out["is_hero"] == 1).sum()),
        "cache_hit": cache_hit,
        "cache_miss": cache_miss,
        "errors": err,
        "elapsed_sec": round(elapsed, 2),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--probe", default="MR_RSI_30")
    p.add_argument("--window", type=int, default=30)
    p.add_argument("--limit", type=int, default=None)

    # fast engine knobs
    p.add_argument("--tail_rows", type=int, default=20000)
    p.add_argument("--fast_cache", action="store_true")
    p.add_argument("--cache_dir", default="cache/hero_scan")

    # two-pass refine
    p.add_argument("--two_pass", action="store_true")
    p.add_argument("--top_k", type=int, default=50)
    p.add_argument("--tail_rows2", type=int, default=None)

    # allocation
    p.add_argument("--allocate", action="store_true")
    p.add_argument("--aum", type=float, default=10_000_000)
    p.add_argument("--alloc_mode", default="equal", choices=["equal", "score"])

    # output control
    p.add_argument("--no_write", action="store_true", help="Do not write hero_scan/allocation CSV files")

    args = p.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    cache_dir = project_root / args.cache_dir

    print(f"[FAST HERO SCAN] probe={args.probe} window={args.window} limit={args.limit} tail_rows={args.tail_rows} cache={args.fast_cache}")
    out = scan_heroes_fast(
        project_root=project_root,
        probe=args.probe,
        window=int(args.window),
        limit=args.limit,
        tail_rows=int(args.tail_rows),
        two_pass=bool(args.two_pass),
        top_k=int(args.top_k),
        tail_rows2=args.tail_rows2,
        allocate=bool(args.allocate),
        aum=float(args.aum),
        alloc_mode=str(args.alloc_mode),
        fast_cache=bool(args.fast_cache),
        cache_dir=cache_dir,
        write_outputs=(not args.no_write),
    )

    print("\n=== FAST SCAN SUMMARY ===")
    for k, v in out.items():
        print(f"- {k}: {v}")
    print("=========================")


if __name__ == "__main__":
    main()
