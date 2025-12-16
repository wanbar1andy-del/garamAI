# scripts/discover_modules.py
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

from garam_core.health.gate import gate_environment, gate_schema, GateSpec
from garam_core.data.loader import load_ohlcv, LoadSpec
from garam_core.data.feature_loader import load_fear_feature, align_fear_to_market


# -----------------------------
# Config
# -----------------------------
SYMBOLS = ["005930"]          # 필요 시 확장
TIMEFRAME = "minute"
TZ = "Asia/Seoul"
YEARS_LOOKBACK = 2

# Event thresholds (초기값; 데이터 기반으로 조정)
FEAR_SPIKE_Q = 0.95
DROP_PCT = -0.012             # -1.2%
VOL_SHOCK_Q = 0.90

HORIZONS_MIN = [60, 120, 180, 240, 360]  # 결과 평가 창


def realized_vol(ret: pd.Series, win: int = 60) -> pd.Series:
    return ret.rolling(win).std() * np.sqrt(win)


def compute_outcomes(px: pd.Series, idx: pd.DatetimeIndex, horizons: list[int]) -> dict:
    """각 horizon에서 평균 수익/최대 역행폭/최적 horizon 산출"""
    res = {}
    for h in horizons:
        # 미래 h분 수익
        fwd = px.shift(-h) / px - 1.0
        res[f"ret_{h}"] = fwd.loc[idx].mean()

        # 최대 역행폭(근사): h분 동안 최저점 대비
        # (정밀 MFE/MAE는 Phase 2에서 개선)
        min_fwd = (px.rolling(h).min().shift(-h+1) / px - 1.0)
        res[f"mdd_{h}"] = min_fwd.loc[idx].mean()
    return res


def bucketize_fear(fear: pd.Series) -> pd.Series:
    return pd.qcut(fear, q=[0, .33, .66, 1.0], labels=["LOW", "MID", "HIGH"])


def main():
    project_root = Path(__file__).resolve().parents[1]
    paths = gate_environment(project_root)

    rows = []

    for sym in SYMBOLS:
        try:
            raw = load_ohlcv(paths.data_root, sym, TIMEFRAME, LoadSpec(tz=TZ))
            mkt = gate_schema(raw, GateSpec(timezone=TZ))
    
            # 2년 컷
            start = mkt.index.max() - pd.DateOffset(years=YEARS_LOOKBACK)
            mkt = mkt.loc[mkt.index >= start]
    
            # fear
            try:
                fear_df = load_fear_feature(paths.data_root, TIMEFRAME, "MARKET")
                fear_aligned = align_fear_to_market(mkt, fear_df)
                fear_bucket = bucketize_fear(fear_aligned["fear_score"])
            except Exception as e:
                print(f"Skipping fear module: {e}")
                fear_aligned = pd.DataFrame({"fear_score": 0.5}, index=mkt.index)
                fear_bucket = pd.Series("MID", index=mkt.index)
    
            # returns & vol
            ret1 = mkt["close"].pct_change()
            vol = realized_vol(ret1, 60)
    
            # Event 1: Fear-Spike Reversal
            fear_thr = fear_aligned["fear_score"].quantile(FEAR_SPIKE_Q)
            vol_thr = vol.quantile(VOL_SHOCK_Q)
            evt = (
                (fear_aligned["fear_score"] >= fear_thr) &
                (ret1 <= DROP_PCT) &
                (vol >= vol_thr)
            )
            evt_idx = mkt.index[evt]
    
            if len(evt_idx) > 10:
                out = compute_outcomes(mkt["close"], evt_idx, HORIZONS_MIN)
                best_h = max(HORIZONS_MIN, key=lambda h: out.get(f"ret_{h}", -1))
                rows.append({
                    "module": "fear_spike_reversal",
                    "symbol": sym,
                    "events": int(evt.sum()),
                    "best_horizon_min": best_h,
                    "exp_return_best": out[f"ret_{best_h}"],
                    "mdd_proxy_best": out[f"mdd_{best_h}"],
                    "fear_bucket_worst": fear_bucket.loc[evt_idx].value_counts().idxmax(),
                })
    
            # Event 2: Vol Squeeze Breakout
            low_vol = vol <= vol.quantile(0.10)
            squeeze = low_vol.rolling(360).sum() >= 300
            breakout = (mkt["close"] > mkt["high"].rolling(120).max().shift(1))
            evt2 = squeeze & breakout
            evt2_idx = mkt.index[evt2]
    
            if len(evt2_idx) > 10:
                out2 = compute_outcomes(mkt["close"], evt2_idx, HORIZONS_MIN)
                best_h2 = max(HORIZONS_MIN, key=lambda h: out2.get(f"ret_{h}", -1))
                rows.append({
                    "module": "vol_squeeze_breakout",
                    "symbol": sym,
                    "events": int(evt2.sum()),
                    "best_horizon_min": best_h2,
                    "exp_return_best": out2[f"ret_{best_h2}"],
                    "mdd_proxy_best": out2[f"mdd_{best_h2}"],
                    "fear_bucket_worst": fear_bucket.loc[evt2_idx].value_counts().idxmax(),
                })
        except Exception as e:
            print(f"Failed processing {sym}: {e}")

    df = pd.DataFrame(rows)
    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "modules_discovery.csv"
    df.to_csv(out_path, index=False)
    print(f"[OK] modules discovery saved: {out_path}")
    print(df)


if __name__ == "__main__":
    main()
