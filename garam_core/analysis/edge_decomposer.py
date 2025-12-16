# garam_core/analysis/edge_decomposer.py
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List

class EdgeDecomposer:
    @staticmethod
    def analyze_trades(
        trades: List[Dict[str, Any]],
        regime_series: Optional[pd.Series] = None,
        timeframe_seconds: Optional[int] = None,  # optional: bar 환산용
    ) -> Dict[str, Any]:
        if not trades:
            return EdgeDecomposer._empty_analysis(["NO_TRADES"])

        df = pd.DataFrame(trades).copy()
        warnings: List[str] = []

        # 1) return_net contract
        if "return_net" not in df.columns:
            warnings.append("MISSING_RETURN_NET: expectancy/quantiles may be invalid")
            return EdgeDecomposer._empty_analysis(warnings)

        r_net = pd.to_numeric(df["return_net"], errors="coerce")
        r_net = r_net.replace([np.inf, -np.inf], np.nan).dropna()
        if r_net.empty:
            return EdgeDecomposer._empty_analysis(["RETURN_NET_ALL_NAN"])

        count = int(r_net.shape[0])
        win_rate = float((r_net > 0).mean())
        avg_r_net = float(r_net.mean())
        median_r_net = float(r_net.median())
        p10_r_net = float(r_net.quantile(0.10))
        p90_r_net = float(r_net.quantile(0.90))

        # 2) tail loss ratio (absolute basis)
        losses = r_net[r_net < 0]
        if losses.empty:
            loss_tail_ratio = 0.0
            max_loss_trade = 0.0
        else:
            max_loss_trade = float(losses.min())
            # worst 10% losses (more negative)
            cutoff = float(losses.quantile(0.10))
            tail_losses = losses[losses <= cutoff]
            loss_tail_ratio = float(tail_losses.abs().sum() / max(1e-12, losses.abs().sum()))

        # 3) hold time
        avg_hold_bars = None
        if "bars_held" in df.columns:
            bh = pd.to_numeric(df["bars_held"], errors="coerce").dropna()
            if not bh.empty:
                avg_hold_bars = float(bh.mean())
        elif "entry_ts" in df.columns and "exit_ts" in df.columns and timeframe_seconds:
            et = pd.to_datetime(df["entry_ts"], utc=True, errors="coerce")
            xt = pd.to_datetime(df["exit_ts"], utc=True, errors="coerce")
            dur = (xt - et).dt.total_seconds()
            dur = dur.replace([np.inf, -np.inf], np.nan).dropna()
            if not dur.empty:
                avg_hold_bars = float((dur / max(1, timeframe_seconds)).mean())
        else:
            warnings.append("MISSING_HOLD_INFO")

        # 4) histogram (clip p1~p99 to avoid outlier dominance)
        lo = float(r_net.quantile(0.01))
        hi = float(r_net.quantile(0.99))
        clipped = r_net.clip(lo, hi)
        hist_counts, bin_edges = np.histogram(clipped, bins=10)

        hist_data = [
            {"bin_start": float(bin_edges[i]), "bin_end": float(bin_edges[i+1]), "count": int(hist_counts[i])}
            for i in range(len(hist_counts))
        ]

        out: Dict[str, Any] = {
            "count": count,
            "win_rate": win_rate,
            "expectancy_net": avg_r_net,
            "avg_r_net": avg_r_net,
            "median_r_net": median_r_net,
            "p10_r_net": p10_r_net,
            "p90_r_net": p90_r_net,
            "avg_hold_bars": avg_hold_bars if avg_hold_bars is not None else 0.0,
            "loss_tail_ratio": loss_tail_ratio,
            "max_loss_trade": max_loss_trade,
            "trade_return_histogram": hist_data,
            "histogram_clipped": True,
            "warnings": warnings,
            "by_regime": {},  # optional future
        }

        return out

    @staticmethod
    def _empty_analysis(warnings: List[str]) -> Dict[str, Any]:
        return {
            "count": 0,
            "win_rate": 0.0,
            "expectancy_net": 0.0,
            "avg_r_net": 0.0,
            "median_r_net": 0.0,
            "p10_r_net": 0.0,
            "p90_r_net": 0.0,
            "avg_hold_bars": 0.0,
            "loss_tail_ratio": 0.0,
            "max_loss_trade": 0.0,
            "trade_return_histogram": [],
            "histogram_clipped": False,
            "warnings": warnings,
            "by_regime": {},
        }
