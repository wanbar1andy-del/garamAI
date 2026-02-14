import argparse
from pathlib import Path
from datetime import datetime, time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

def _regime_label(r60: float) -> str:
    if not np.isfinite(r60):
        return "NA"
    if r60 >= 0.002:
        return "UP"
    if r60 <= -0.002:
        return "DOWN"
    return "FLAT"

def _price_at(series: pd.Series, ts: pd.Timestamp) -> float:
    if ts in series.index:
        v = series.loc[ts]
        return float(v) if np.isfinite(v) else np.nan
    i = series.index.searchsorted(ts, side="right") - 1
    if i < 0:
        return np.nan
    return float(series.iloc[i])

def _load_minute_close(project_root: Path, data_root: Path, symbol: str) -> pd.Series:
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from garam_core.data.loader import load_ohlcv  # type: ignore

    df = load_ohlcv(data_root, symbol, "minute")
    if df is None or df.empty:
        return pd.Series(dtype=float)
    df = df.reset_index()
    if "index" in df.columns and "date" not in df.columns:
        df.rename(columns={"index": "date"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    if "date" not in df.columns or "close" not in df.columns:
        return pd.Series(dtype=float)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values("date")
    s = df.set_index("date")["close"].astype(float)
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle_csv", required=True)
    ap.add_argument("--out_dir", required=True)

    ap.add_argument("--thr_list", type=str, default="-0.002,0.0,0.002,0.005")
    ap.add_argument("--proxy_symbol", type=str, default="005930")
    ap.add_argument("--data_root", type=str, default="GARAM_Data")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.oracle_csv)
    df["ts"] = pd.to_datetime(df["ts"])
    # ts,horizon 별 top1은 oracle_top1_net 컬럼(각 row에 복제됨)
    top1 = df.dropna(subset=["oracle_top1_net"]).groupby(["ts", "horizon_min"])["oracle_top1_net"].max().reset_index()

    if top1.empty:
        raise RuntimeError("oracle_top1_net is empty. Check oracle generation (topk and dates).")

    thr_list = [float(x.strip()) for x in args.thr_list.split(",") if x.strip()]
    horizons = sorted(top1["horizon_min"].unique().tolist())

    # regime by proxy 60m return at ts
    project_root = Path(__file__).resolve().parents[2]
    proxy = str(args.proxy_symbol).zfill(6)
    close = _load_minute_close(project_root, project_root / args.data_root, proxy)
    if close.empty:
        # fallback: regime from oracle top1 itself (weak proxy)
        top1["regime"] = top1["oracle_top1_net"].apply(_regime_label)
    else:
        def reg(ts):
            p0 = _price_at(close, ts)
            p1 = _price_at(close, ts + pd.Timedelta(minutes=60))
            r60 = (p1/p0 - 1.0) if (np.isfinite(p0) and np.isfinite(p1) and p0>0) else np.nan
            return _regime_label(r60)
        top1["regime"] = top1["ts"].apply(reg)

    rows = []
    for H in horizons:
        dH = top1[top1["horizon_min"] == H].copy()
        for thr in thr_list:
            rate = float((dH["oracle_top1_net"] >= thr).mean() * 100)
            rows.append({"horizon_min": H, "thr": thr, "hero_exists_rate_pct": rate})
    df_rate = pd.DataFrame(rows)
    df_rate.to_csv(out_dir / "hero_exists_rate.csv", index=False, encoding="utf-8-sig")

    # plot: hero exists curves per horizon
    plt.figure()
    for H in horizons:
        dH = df_rate[df_rate["horizon_min"] == H].sort_values("thr")
        plt.plot(dH["thr"].values, dH["hero_exists_rate_pct"].values, label=f"H={H}m")
    plt.title("Hero Exists Rate vs Threshold (OracleTop1Net)")
    plt.xlabel("Threshold (net return)")
    plt.ylabel("Hero Exists Rate (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "hero_exists_curve.png")
    plt.close()

    # regime breakdown at thr=0 (default)
    thr0 = 0.0
    d0 = top1.copy()
    d0["hero"] = (d0["oracle_top1_net"] >= thr0).astype(int)
    reg = d0.groupby(["horizon_min", "regime"])["hero"].mean().reset_index()
    reg["hero_exists_rate_pct"] = reg["hero"] * 100
    reg.to_csv(out_dir / "hero_exists_by_regime_thr0.csv", index=False, encoding="utf-8-sig")

    # plot by regime (bar per horizon)
    for H in horizons:
        dH = reg[reg["horizon_min"] == H].copy()
        if dH.empty:
            continue
        plt.figure()
        plt.bar(dH["regime"].values, dH["hero_exists_rate_pct"].values)
        plt.title(f"Hero Exists Rate by Regime (thr=0) H={H}m")
        plt.ylabel("Rate (%)")
        plt.tight_layout()
        plt.savefig(out_dir / f"hero_exists_by_regime_thr0_H{H}.png")
        plt.close()

    print(f"[OK] {out_dir}")

if __name__ == "__main__":
    main()
