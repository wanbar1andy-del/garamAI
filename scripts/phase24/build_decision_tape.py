import argparse
from pathlib import Path
from datetime import datetime, time
import pandas as pd
import numpy as np
import sys

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from garam_core.data.loader import load_ohlcv

def _load_minute_df(data_root: Path, symbol: str) -> pd.DataFrame:
    df = load_ohlcv(data_root, symbol, "minute")
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    if "index" in df.columns and "date" not in df.columns:
        df.rename(columns={"index": "date"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    if "date" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)
    return df

def _day_slice(df: pd.DataFrame, day: pd.Timestamp) -> pd.DataFrame:
    start = day
    end = day + pd.Timedelta(days=1)
    i0 = df["date"].searchsorted(start)
    i1 = df["date"].searchsorted(end)
    if i0 == i1:
        return pd.DataFrame()
    return df.iloc[i0:i1].copy()

def _make_full_index(day_date) -> pd.DatetimeIndex:
    st = datetime.combine(day_date, time(9, 0))
    en = datetime.combine(day_date, time(15, 30))
    return pd.date_range(st, en, freq="1min")

def _daily_ma60_from_minute(df_all: pd.DataFrame) -> pd.Series:
    tmp = df_all.set_index("date")
    daily_close = tmp["close"].resample("D").last().dropna()
    return daily_close.rolling(60).mean()

def _asof_ma60(ma60_series: pd.Series, day: pd.Timestamp) -> float:
    if ma60_series is None or ma60_series.empty:
        return np.nan
    idx = ma60_series.index.searchsorted(pd.Timestamp(day), side="right") - 1
    if idx < 0:
        return np.nan
    return float(ma60_series.iloc[idx])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start_date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end_date", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--anchor_min", type=int, default=5)
    ap.add_argument("--max_horizon", type=int, default=60, help="SSOT: 앵커 끝시간 컷에 쓰는 최대 H(min)")
    ap.add_argument("--topn", type=int, default=20, help="ts별 상위 N 후보 저장")
    ap.add_argument("--entry_roc", type=float, default=-0.02)
    ap.add_argument("--entry_vol", type=float, default=1.2)
    ap.add_argument("--out_tag", type=str, default="phase24_tape")
    ap.add_argument("--symbols_csv", type=str, default="GARAM_Data/real_universe_400.csv")
    ap.add_argument("--symbols_limit", type=int, default=0)
    args = ap.parse_args()

    data_root = project_root / "GARAM_Data"
    univ_path = project_root / args.symbols_csv

    df_univ = pd.read_csv(univ_path)
    raw = df_univ["Code"].astype(str).tolist()
    symbols = [c.zfill(6) for c in raw if c.zfill(6).isdigit() and len(c.zfill(6)) == 6]
    if "475960" in symbols:
        symbols.remove("475960")
    if args.symbols_limit and args.symbols_limit > 0:
        symbols = symbols[: args.symbols_limit]

    start = pd.to_datetime(args.start_date)
    end = pd.to_datetime(args.end_date)
    days = pd.date_range(start, end, freq="B")

    out_base = project_root / "results" / "phase24" / "tape" / args.out_tag
    out_base.mkdir(parents=True, exist_ok=True)

    # preload minute + ma60
    data_map, ma60_map = {}, {}
    for i, sym in enumerate(symbols, 1):
        if i % 50 == 0:
            print(f"[LOAD] {i}/{len(symbols)}")
        df = _load_minute_df(data_root, sym)
        if df.empty:
            continue
        data_map[sym] = df
        ma60_map[sym] = _daily_ma60_from_minute(df)

    rows = []

    for day in days:
        day_date = day.date()
        full_idx = _make_full_index(day_date)
        pos_map = {ts: i for i, ts in enumerate(full_idx)}
        n_min = len(full_idx)

        # ===== SSOT: Anchor End = session_end - max_horizon =====
        session_end = datetime.combine(day_date, time(15, 30))
        anchor_end = session_end - pd.Timedelta(minutes=int(args.max_horizon))
        anchors = pd.date_range(
            datetime.combine(day_date, time(9, 5)),
            anchor_end,
            freq=f"{args.anchor_min}min"
        )
        anchor_pos = [(ts, pos_map[ts]) for ts in anchors if ts in pos_map]

        # day cache: per symbol features arrays (compute once/day/symbol)
        day_feat = {}
        for sym, df_all in data_map.items():
            df_day = _day_slice(df_all, day)
            if df_day.empty:
                continue

            s = df_day.set_index("date").reindex(full_idx)
            s["close"] = s["close"].ffill()
            s["volume"] = s["volume"].fillna(0)

            close = s["close"].astype(float)
            vol = s["volume"].astype(float)

            # MA60 regime check (asof)
            ma60_val = _asof_ma60(ma60_map.get(sym), day)
            if not np.isfinite(ma60_val) or ma60_val <= 0:
                continue

            # features
            roc_5m = (close / close.shift(5)) - 1.0

            vol_roll = vol.rolling(10).sum()
            vol_ma = vol_roll / 10.0
            vol_accel = np.divide(vol, vol_ma, out=np.zeros_like(vol_ma), where=vol_ma > 1e-9)

            # reversal flags (score booster)
            rev_2c = (close > close.shift(1)) & (close.shift(1) > close.shift(2))
            recent_max = close.shift(1).rolling(3).max()
            rev_brk = close > recent_max

            day_feat[sym] = {
                "close": close.to_numpy(dtype=np.float64),
                "roc_5m": roc_5m.to_numpy(dtype=np.float64),
                "vol_accel": np.asarray(vol_accel, dtype=np.float64),
                "rev_2c": rev_2c.to_numpy(dtype=bool),
                "rev_brk": rev_brk.to_numpy(dtype=bool),
                "ma60": float(ma60_val),
            }

        for ts, p in anchor_pos:
            cand_list = []

            for sym, feat in day_feat.items():
                c = feat["close"][p]
                if not np.isfinite(c):
                    continue
                # trend mask
                if c <= feat["ma60"]:
                    continue

                r = feat["roc_5m"][p]
                v = feat["vol_accel"][p]
                if not np.isfinite(r) or not np.isfinite(v):
                    continue

                pass_gate = (r <= args.entry_roc) and (v >= args.entry_vol)
                if not pass_gate:
                    continue

                dip_strength = min(max((-r) / abs(args.entry_roc), 0.0), 2.0)
                vol_score = float(np.log1p(v))
                rev_bonus = (0.2 if feat["rev_2c"][p] else 0.0) + (0.25 if feat["rev_brk"][p] else 0.0)
                score = dip_strength + vol_score + rev_bonus

                cand_list.append((sym, score, r, v, int(feat["rev_2c"][p]), int(feat["rev_brk"][p]), feat["ma60"]))

            if not cand_list:
                rows.append({
                    "ts": ts, "rank": 0, "symbol": "", "score": np.nan,
                    "roc_5m": np.nan, "vol_accel": np.nan,
                    "rev_2c": 0, "rev_brk": 0,
                    "ma60": np.nan, "n_cands": 0
                })
                continue

            cand_list.sort(key=lambda x: x[1], reverse=True)
            n_cands = len(cand_list)

            for rank, (sym, score, r, v, rev2, revb, ma60v) in enumerate(cand_list[: args.topn], 1):
                rows.append({
                    "ts": ts,
                    "rank": rank,
                    "symbol": sym,
                    "score": float(score),
                    "roc_5m": float(r),
                    "vol_accel": float(v),
                    "rev_2c": int(rev2),
                    "rev_brk": int(revb),
                    "ma60": float(ma60v),
                    "n_cands": int(n_cands),
                })

        print(f"[DAY] {day.date()} done | anchors={len(anchor_pos)} | syms_day={len(day_feat)}")

    df_out = pd.DataFrame(rows)
    df_out["ts"] = pd.to_datetime(df_out["ts"])
    out_csv = out_base / f"decision_tape_{args.start_date}_{args.end_date}.csv"
    df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] {out_csv}")

if __name__ == "__main__":
    main()
