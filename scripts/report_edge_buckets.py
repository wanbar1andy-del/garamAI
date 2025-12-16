# scripts/report_edge_buckets.py
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.health.gate import gate_environment, gate_schema, GateSpec
from garam_core.data.loader import load_ohlcv, LoadSpec
from garam_core.engine.edge import edge_score


def compute_edge_series(df: pd.DataFrame, window: int = 300) -> pd.Series:
    # 비용 때문에 루프이지만 2년 분봉이면 충분히 감당 가능(필요 시 최적화)
    es = []
    idx = df.index
    # We need a rolling window. 
    # To be efficient, we might want to vectorize or just optimize the loop.
    # For 200,000 bars, loop is slow in Python.
    # But edge_score inside uses rolling. 
    # IF edge_score was vectorized on full DF, it would be fast.
    # Current edge_score takes a window.
    # Let's see if we can call it on full DF.
    # The edge_score fn handles full DF rolling internally.
    # BUT `_z` uses rolling mean/std.
    # If we pass the WHOLE DF to logic similar to edge_score, we get a Series!
    # Let's re-implement vectorized version here for speed report.
    
    c = df["close"]
    v = df["volume"] if "volume" in df.columns else None

    r1 = c.pct_change()
    mom = r1.rolling(30).sum()
    acc = mom.diff(10)
    vol = r1.rolling(60).std()
    
    # Z-scores over 240 window
    def z_vec(s, n):
        return (s - s.rolling(n).mean()) / s.rolling(n).std().replace(0, np.nan)

    mom_z = z_vec(mom, 240)
    acc_z = z_vec(acc, 240)
    vol_z = z_vec(vol, 240)
    
    if v is not None:
        vs = z_vec(v, 240)
    else:
        vs = pd.Series(0.0, index=c.index)

    raw = 0.9 * np.tanh(mom_z.fillna(0)) + 0.6 * np.tanh(acc_z.fillna(0)) \
          - 0.4 * np.tanh(vol_z.fillna(0)) + 0.2 * np.tanh(vs.fillna(0))

    s = 0.5 + 0.5 * np.tanh(raw)
    return s.clip(0.0, 1.0)


def main():
    project_root = Path(__file__).resolve().parents[1]
    paths = gate_environment(project_root)

    symbol = sys.argv[1] if len(sys.argv) >= 2 else "005930"
    timeframe = sys.argv[2] if len(sys.argv) >= 3 else "minute"
    tz = sys.argv[3] if len(sys.argv) >= 4 else "Asia/Seoul"
    horizons = [60, 120, 240, 360]

    print(f"Loading {symbol}...")
    raw = load_ohlcv(paths.data_root, symbol, timeframe, LoadSpec(tz=tz))
    df = gate_schema(raw, GateSpec(timezone=tz))

    print("Computing Edge Score Series...")
    edge = compute_edge_series(df).dropna()
    
    # Align
    common = df.index.intersection(edge.index)
    df = df.loc[common]
    edge = edge.loc[common]
    c = df["close"]

    out_rows = []
    # 분위
    try:
        buckets = pd.qcut(edge, q=[0, .33, .66, 1.0], labels=["LOW", "MID", "HIGH"])
    except ValueError:
        print("Not enough unique edge values for qcut.")
        return

    print("Analyzing Buckets...")
    for b in ["LOW", "MID", "HIGH"]:
        idx = buckets.index[buckets == b]
        if len(idx) < 100:
            continue

        for h in horizons:
            # Future return
            fwd = c.shift(-h) / c - 1.0
            # Max DD proxy (min in next h bars)
            # Rolling max/min is tricky with forward looking.
            # rolling(h).min().shift(-h+1) is correct for "min from now to h-1 ahead"
            min_future = c.rolling(h).min().shift(-h+1)
            mdd_proxy = (min_future / c - 1.0)

            out_rows.append({
                "symbol": symbol,
                "bucket": b,
                "horizon_min": h,
                "count": int(len(idx)),
                "exp_return_mean": float(fwd.loc[idx].mean()),
                "mdd_proxy_mean": float(mdd_proxy.loc[idx].mean()),
                "edge_mean": float(edge.loc[idx].mean()),
            })

    out = pd.DataFrame(out_rows)
    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"edge_bucket_report_{symbol}.csv"
    out.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[OK] saved: {out_path}")
    print(out)


if __name__ == "__main__":
    main()
