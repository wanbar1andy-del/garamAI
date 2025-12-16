# scripts/research/pulse/analyze_hold_ev.py
from __future__ import annotations

import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

# Ensure garam_core is importable
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from garam_core.strategy.registry import discover_strategies
from garam_core.backtest.engine_unified import run_backtest_unified
from garam_core.research.pulse.load_data import load_minute_data, enhance_features


def _hold_bars_from_trade_log(trade_log: pd.DataFrame, df_index: pd.Index) -> pd.Series:
    """
    entry_time / exit_time를 df_index 기준 바 위치로 매핑하여 hold_bars 산출
    - minute 데이터면 hold_bars ~ hold_minutes에 대응
    """
    # df_index가 DatetimeIndex이면 entry/exit도 Datetime
    # get_indexer를 통해 가장 가까운 위치를 찾음 (정확히 일치하는 게 최선)
    entry_pos = df_index.get_indexer(pd.to_datetime(trade_log["entry_time"]), method="nearest")
    exit_pos = df_index.get_indexer(pd.to_datetime(trade_log["exit_time"]), method="nearest")
    hold = (exit_pos - entry_pos).clip(min=1)
    return pd.Series(hold, index=trade_log.index, dtype="int64")


def _bucketize(hold_bars: pd.Series, bucket: int) -> pd.Series:
    """
    hold_bars를 bucket 단위로 구간화.
    예: bucket=5이면 1~5, 6~10, 11~15 ...
    """
    b = ((hold_bars - 1) // bucket + 1) * bucket
    return b


def summarize_by_hold(trade_log: pd.DataFrame, hold_bars: pd.Series, bucket: int) -> pd.DataFrame:
    df = trade_log.copy()
    df["hold_bars"] = hold_bars
    df["hold_bucket"] = _bucketize(hold_bars, bucket)

    # 승/패
    df["is_win"] = (df["pnl_net"] > 0).astype(int)

    # 구간별 집계
    g = df.groupby("hold_bucket", as_index=False).agg(
        trades=("pnl_net", "count"),
        win_rate=("is_win", "mean"),
        ev_mean=("pnl_net", "mean"),            # 비용 포함 기대값(핵심)
        gross_mean=("return_gross", "mean"),    # 비용 전 평균
        cost_mean=("cost_paid", "mean"),
        pnl_sum=("pnl_net", "sum"),
        win_sum=("pnl_net", lambda x: x[x > 0].sum()),
        loss_sum=("pnl_net", lambda x: x[x <= 0].sum()),
        hold_mean=("hold_bars", "mean"),
    )

    # profit factor
    g["profit_factor"] = np.where(g["loss_sum"] < 0, abs(g["win_sum"] / g["loss_sum"]), np.inf)

    # 누적 EV (학습용: hold 짧은 구간부터 누적하면 "유통기한"이 보임)
    g = g.sort_values("hold_bucket")
    g["ev_cum"] = g["pnl_sum"].cumsum()
    g["trades_cum"] = g["trades"].cumsum()
    g["ev_cum_mean"] = g["ev_cum"] / g["trades_cum"]

    # 보기 좋게
    g["win_rate"] = g["win_rate"].astype(float)
    g["ev_mean"] = g["ev_mean"].astype(float)
    g["gross_mean"] = g["gross_mean"].astype(float)
    g["cost_mean"] = g["cost_mean"].astype(float)
    g["profit_factor"] = g["profit_factor"].astype(float)
    return g


def plot_hold_ev(summary: pd.DataFrame, out_dir: Path, title_prefix: str, bucket: int):
    out_dir.mkdir(parents=True, exist_ok=True)

    x = summary["hold_bucket"].values

    # 1) EV(mean pnl_net) vs holding bucket
    plt.figure()
    plt.plot(x, summary["ev_mean"].values, marker="o")
    plt.axhline(0.0, linewidth=1)

    # EV 양수 구간 강조(시각적)
    pos_mask = summary["ev_mean"].values > 0
    if pos_mask.any():
        plt.scatter(x[pos_mask], summary["ev_mean"].values[pos_mask])

    plt.title(f"{title_prefix} | EV(mean pnl_net) by Hold Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("EV (mean pnl_net)")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_ev.png", dpi=150)
    plt.close()

    # 2) WinRate vs holding bucket
    plt.figure()
    plt.plot(x, summary["win_rate"].values, marker="o")
    plt.title(f"{title_prefix} | WinRate by Hold Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("WinRate")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_winrate.png", dpi=150)
    plt.close()

    # 3) ProfitFactor vs holding bucket
    plt.figure()
    plt.plot(x, summary["profit_factor"].values, marker="o")
    plt.title(f"{title_prefix} | Profit Factor by Hold Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("Profit Factor")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_profit_factor.png", dpi=150)
    plt.close()

    # 4) Cumulative EV mean (짧은 홀딩부터 누적)
    plt.figure()
    plt.plot(x, summary["ev_cum_mean"].values, marker="o")
    plt.axhline(0.0, linewidth=1)
    plt.title(f"{title_prefix} | Cumulative EV Mean up to Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("Cumulative EV Mean")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_ev_cum_mean.png", dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="005930")
    parser.add_argument("--strategy", default="mean_reversion", help="strategy NAME to analyze")
    parser.add_argument("--data_dir", default=str(PROJECT_ROOT / "GARAM_Data/minute/kr"))
    parser.add_argument("--bucket", type=int, default=5, help="hold bucket size (bars)")
    parser.add_argument("--out_dir", default=str(PROJECT_ROOT / "reports" / "pulse_hold_ev"))
    args = parser.parse_args()

    symbol = args.symbol
    strat_name = args.strategy
    bucket = int(args.bucket)
    out_dir = Path(args.out_dir) / f"{symbol}_{strat_name}"

    # 1) data
    df = load_minute_data(symbol, args.data_dir)
    df = enhance_features(df)

    # 2) find strategy
    strategies = discover_strategies()
    strat_map = {s.NAME: s for s in strategies}
    if strat_name not in strat_map:
        raise ValueError(f"Strategy not found: {strat_name}. Found: {list(strat_map.keys())}")

    strat = strat_map[strat_name]()

    # 3) backtest
    res = run_backtest_unified(strat, df)
    trade_log = res.get("trade_log")

    if trade_log is None or len(trade_log) == 0:
        print("No trades found. Nothing to analyze.")
        return

    # 4) holding bars
    # engine_unified의 trade_log 컬럼 확인 (pnl_net, entry_time, exit_time)
    # 만약 cost/gross 없으면 runner에서는 계산 안함 (analyze에서는 trade_log만 있으면 됨)
    # 하지만 runner 로직에 맞춰서 보완 필요하면 여기서 해줄 수 있음.
    # analyze_hold_ev는 standalone이라 자체적으로 처리하거나 pulse_ev_runner의 함수를 쓸 수 있음.
    # 여기서는 독립적으로 구현됨.
    
    if "pnl_net" not in trade_log.columns:
         print("Error: trade_log missing 'pnl_net'")
         return

    hold_bars = _hold_bars_from_trade_log(trade_log, df.index)
    
    # ensure columns for summary
    if "return_gross" not in trade_log.columns:
        if "return_pct" in trade_log.columns:
            trade_log["return_gross"] = trade_log["return_pct"]
        else:
            trade_log["return_gross"] = np.nan
            
    if "cost_paid" not in trade_log.columns:
        trade_log["cost_paid"] = 0.0031 # approx

    summary = summarize_by_hold(trade_log, hold_bars, bucket)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "hold_ev_summary.csv", index=False, encoding="utf-8-sig")

    title_prefix = f"{symbol} / {strat_name}"
    plot_hold_ev(summary, out_dir, title_prefix, bucket)

    print(f"[OK] Saved: {out_dir / 'hold_ev_summary.csv'}")
    print(f"[OK] Plots: hold_ev.png, hold_winrate.png, hold_profit_factor.png, hold_ev_cum_mean.png")


if __name__ == "__main__":
    main()
