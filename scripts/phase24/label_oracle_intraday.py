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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start_date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end_date", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--anchor_min", type=int, default=5)
    ap.add_argument("--horizons", type=str, default="10,30,60")
    ap.add_argument("--topk", type=int, default=400, help="ts별 상위 K 저장(권고: 400=전종목)")
    ap.add_argument("--out_tag", type=str, default="phase24_oracle")
    ap.add_argument("--symbols_csv", type=str, default="GARAM_Data/real_universe_400.csv")
    ap.add_argument("--cost_rt", type=float, default=0.0030, help="SSOT roundtrip cost 근사(기본 30bps)")
    ap.add_argument("--mkt_symbol", type=str, default="005930", help="레짐용 마켓 프록시 심볼")
    ap.add_argument("--mkt_regime_h", type=int, default=60, help="레짐 분류에 쓰는 horizon(min)")
    ap.add_argument("--symbols_limit", type=int, default=0, help="디버그용 심볼 수 제한(0=전체)")
    args = ap.parse_args()

    horizons = [int(x.strip()) for x in args.horizons.split(",") if x.strip()]
    if not horizons:
        raise ValueError("horizons is empty")

    max_h = max(horizons)

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

    out_base = project_root / "results" / "phase24" / "oracle" / args.out_tag
    out_base.mkdir(parents=True, exist_ok=True)

    # preload minute data
    data_map = {}
    for i, sym in enumerate(symbols, 1):
        if i % 50 == 0:
            print(f"[LOAD] {i}/{len(symbols)}")
        df = _load_minute_df(data_root, sym)
        if not df.empty:
            data_map[sym] = df

    # ensure market symbol loaded (for regime)
    if args.mkt_symbol not in data_map:
        df_mkt = _load_minute_df(data_root, args.mkt_symbol)
        if not df_mkt.empty:
            data_map[args.mkt_symbol] = df_mkt

    syms = list(data_map.keys())
    if args.mkt_symbol not in syms:
        print(f"[WARN] mkt_symbol {args.mkt_symbol} not available. Regime will be NA.")

    all_rows = []

    for day in days:
        day_date = day.date()
        full_idx = _make_full_index(day_date)
        n_min = len(full_idx)

        # ===== SSOT: Anchor End = session_end - max_horizon =====
        session_end = datetime.combine(day_date, time(15, 30))
        anchor_end = session_end - pd.Timedelta(minutes=max_h)
        anchors = pd.date_range(
            datetime.combine(day_date, time(9, 5)),
            anchor_end,
            freq=f"{args.anchor_min}min"
        )

        # map ts -> minute position
        pos_map = {ts: i for i, ts in enumerate(full_idx)}
        anchor_pos = [(ts, pos_map[ts]) for ts in anchors if ts in pos_map]

        # build per-day close matrix (syms x minutes)
        # NOTE: ffill 이후에도 시작구간 NaN이 남을 수 있음 (해당 심볼은 해당 ts에서 제외)
        mat = np.full((len(syms), n_min), np.nan, dtype=np.float64)
        for si, sym in enumerate(syms):
            df_all = data_map[sym]
            df_day = _day_slice(df_all, day)
            if df_day.empty:
                continue
            s = df_day.set_index("date").reindex(full_idx)
            s["close"] = s["close"].ffill()
            mat[si, :] = s["close"].to_numpy(dtype=np.float64)

        # market 60m return for regime (raw 기준)
        mkt_r60_map = {}
        if args.mkt_symbol in syms and args.mkt_regime_h > 0:
            try:
                mi = syms.index(args.mkt_symbol)
                m_close = mat[mi, :]
                Hm = args.mkt_regime_h
                if Hm < n_min:
                    m_raw = (m_close[Hm:] / m_close[:-Hm]) - 1.0
                    # anchor pos 기준으로 lookup
                    for ts, p in anchor_pos:
                        if p < len(m_raw) and np.isfinite(m_raw[p]):
                            mkt_r60_map[ts] = float(m_raw[p])
                        else:
                            mkt_r60_map[ts] = np.nan
            except Exception:
                pass

        # for each horizon
        for H in horizons:
            if H >= n_min:
                continue

            raw_ret_mat = (mat[:, H:] / mat[:, :-H]) - 1.0  # shape: (syms, n_min-H)

            for ts, p in anchor_pos:
                if p >= raw_ret_mat.shape[1]:
                    continue

                raw_vec = raw_ret_mat[:, p]
                valid = np.isfinite(raw_vec)

                if not np.any(valid):
                    all_rows.append({
                        "ts": ts, "horizon_min": H, "symbol": "",
                        "raw_ret": np.nan, "net_ret": np.nan,
                        "rank": 0, "topk": args.topk,
                        "oracle_top1_net": np.nan,
                        "n_symbols": 0,
                        "mkt_raw_ret_60": mkt_r60_map.get(ts, np.nan),
                    })
                    continue

                raw_vec_v = raw_vec[valid]
                syms_v = np.array(syms, dtype=object)[valid]
                net_vec_v = raw_vec_v - float(args.cost_rt)

                # oracle top1
                top1_net = float(np.max(net_vec_v))

                # TopK selection
                k = min(int(args.topk), len(net_vec_v))
                if k <= 0:
                    k = len(net_vec_v)

                # partial sort then sort within topk
                idx_part = np.argpartition(-net_vec_v, k - 1)[:k]
                idx_sorted = idx_part[np.argsort(-net_vec_v[idx_part])]

                for rnk, j in enumerate(idx_sorted, 1):
                    all_rows.append({
                        "ts": ts,
                        "horizon_min": H,
                        "symbol": str(syms_v[j]),
                        "raw_ret": float(raw_vec_v[j]),
                        "net_ret": float(net_vec_v[j]),
                        "rank": rnk,
                        "topk": int(args.topk),
                        "oracle_top1_net": top1_net,
                        "n_symbols": int(len(net_vec_v)),
                        "mkt_raw_ret_60": mkt_r60_map.get(ts, np.nan),
                    })

        print(f"[DAY] {day.date()} done | anchors={len(anchor_pos)}")

    df_out = pd.DataFrame(all_rows)
    df_out["ts"] = pd.to_datetime(df_out["ts"])
    out_csv = out_base / f"oracle_labels_{args.start_date}_{args.end_date}.csv"
    df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] {out_csv}")

if __name__ == "__main__":
    main()
