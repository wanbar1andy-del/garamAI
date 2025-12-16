# scripts/research/pulse_ev_runner.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _hold_bars_from_trade_log(trade_log: pd.DataFrame, df_index: pd.Index) -> pd.Series:
    entry = pd.to_datetime(trade_log["entry_time"])
    exit_ = pd.to_datetime(trade_log["exit_time"])
    entry_pos = df_index.get_indexer(entry, method="nearest")
    exit_pos = df_index.get_indexer(exit_, method="nearest")
    hold = (exit_pos - entry_pos).clip(min=1)
    return pd.Series(hold, index=trade_log.index, dtype="int64")


def _bucketize(hold_bars: pd.Series, bucket: int) -> pd.Series:
    b = ((hold_bars - 1) // bucket + 1) * bucket
    return b


def _ensure_cols(trade_log: pd.DataFrame, cost_per_trade: float = 0.0031) -> pd.DataFrame:
    """
    engine_unified 버전에 따라 컬럼이 다를 수 있으니, 분석에 필요한 컬럼을 보완.
    - pnl_net: 필수
    - return_gross: 없으면 return_pct를 gross로 사용
    - cost_paid: 없으면 trade당 cost_per_trade로 가정(근사)
    """
    df = trade_log.copy()
    if "pnl_net" not in df.columns:
        raise ValueError("trade_log must contain 'pnl_net'.")

    if "return_gross" not in df.columns:
        if "return_pct" in df.columns:
            df["return_gross"] = df["return_pct"]
        else:
            df["return_gross"] = np.nan

    if "cost_paid" not in df.columns:
        # trade당 고정비용 근사(왕복)
        df["cost_paid"] = cost_per_trade

    return df


def summarize_by_hold(trade_log: pd.DataFrame, hold_bars: pd.Series, bucket: int) -> pd.DataFrame:
    df = trade_log.copy()
    df["hold_bars"] = hold_bars
    df["hold_bucket"] = _bucketize(hold_bars, bucket)
    df["is_win"] = (df["pnl_net"] > 0).astype(int)

    g = df.groupby("hold_bucket", as_index=False).agg(
        trades=("pnl_net", "count"),
        win_rate=("is_win", "mean"),
        ev_mean=("pnl_net", "mean"),
        pnl_sum=("pnl_net", "sum"),
        gross_mean=("return_gross", "mean"),
        cost_mean=("cost_paid", "mean"),
        win_sum=("pnl_net", lambda x: x[x > 0].sum()),
        loss_sum=("pnl_net", lambda x: x[x <= 0].sum()),
        hold_mean=("hold_bars", "mean"),
    )

    g["profit_factor"] = np.where(g["loss_sum"] < 0, abs(g["win_sum"] / g["loss_sum"]), np.inf)

    g = g.sort_values("hold_bucket")
    g["ev_cum"] = g["pnl_sum"].cumsum()
    g["trades_cum"] = g["trades"].cumsum()
    g["ev_cum_mean"] = g["ev_cum"] / g["trades_cum"]

    return g


def plot_hold_ev(summary: pd.DataFrame, out_dir: Path, title_prefix: str, bucket: int):
    out_dir.mkdir(parents=True, exist_ok=True)
    x = summary["hold_bucket"].values

    # EV by hold
    plt.figure()
    plt.plot(x, summary["ev_mean"].values, marker="o")
    plt.axhline(0.0, linewidth=1)
    pos_mask = summary["ev_mean"].values > 0
    if pos_mask.any():
        plt.scatter(x[pos_mask], summary["ev_mean"].values[pos_mask])
    plt.title(f"{title_prefix} | EV(mean pnl_net) by Hold Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("EV (mean pnl_net)")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_ev.png", dpi=150)
    plt.close()

    # WinRate
    plt.figure()
    plt.plot(x, summary["win_rate"].values, marker="o")
    plt.title(f"{title_prefix} | WinRate by Hold Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("WinRate")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_winrate.png", dpi=150)
    plt.close()

    # ProfitFactor
    plt.figure()
    plt.plot(x, summary["profit_factor"].values, marker="o")
    plt.title(f"{title_prefix} | Profit Factor by Hold Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("Profit Factor")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_profit_factor.png", dpi=150)
    plt.close()

    # Cumulative EV mean
    plt.figure()
    plt.plot(x, summary["ev_cum_mean"].values, marker="o")
    plt.axhline(0.0, linewidth=1)
    plt.title(f"{title_prefix} | Cumulative EV Mean up to Bucket (bucket={bucket})")
    plt.xlabel("Hold Bucket (bars)")
    plt.ylabel("Cumulative EV Mean")
    plt.tight_layout()
    plt.savefig(out_dir / "hold_ev_cum_mean.png", dpi=150)
    plt.close()


def pick_top_strategies(summary_csv: Path, top_n: int = 3) -> List[str]:
    df = pd.read_csv(summary_csv)
    # survivable 우선: abs(mdd) 작은 순으로 1차 필터, 그 중 roi 큰 순
    df["mdd_abs"] = df["max_drawdown"].abs()
    df = df.sort_values(["roi", "mdd_abs"], ascending=[False, True])
    return df["strategy"].head(top_n).tolist()


def run_pulse_ev_for_results(
    results: List[dict],
    symbol: str,
    df_index: pd.Index,
    out_base: Path,
    bucket: int = 5,
    cost_per_trade: float = 0.0031,
) -> Dict[str, Path]:
    """
    results: run_backtest_unified 결과 리스트(각각 dict, trade_log 포함)
    symbol  : 분석 대상 심볼
    out_base: reports/pulse_hold_ev/ 아래 저장
    반환: 전략명 -> 산출물 디렉터리
    """
    out_map: Dict[str, Path] = {}
    for r in results:
        if r.get("symbol") != symbol:
            continue
        strat = r.get("strategy")
        tlog = r.get("trade_log")
        if tlog is None or len(tlog) == 0:
            continue

        tlog = _ensure_cols(tlog, cost_per_trade=cost_per_trade)

        hold = _hold_bars_from_trade_log(tlog, df_index)
        summ = summarize_by_hold(tlog, hold, bucket=bucket)

        out_dir = out_base / f"{symbol}_{strat}"
        out_dir.mkdir(parents=True, exist_ok=True)
        summ.to_csv(out_dir / "hold_ev_summary.csv", index=False, encoding="utf-8-sig")
        plot_hold_ev(summ, out_dir, title_prefix=f"{symbol}/{strat}", bucket=bucket)

        out_map[strat] = out_dir

    return out_map


def inject_pulse_section(report_md_path: Path, symbol: str, strat_dirs: Dict[str, Path]):
    """
    report.md 끝에 Pulse EV 분석 섹션을 추가(중복 방지 위해 marker 사용).
    """
    marker = "\n\n## Pulse Hold-EV Analysis\n"
    text = report_md_path.read_text(encoding="utf-8") if report_md_path.exists() else ""

    # 기존 섹션 제거 후 재삽입(간단)
    if "## Pulse Hold-EV Analysis" in text:
        text = text.split("## Pulse Hold-EV Analysis")[0].rstrip() + "\n"

    lines = [text.rstrip(), marker]
    lines.append(f"- Symbol: `{symbol}`")
    lines.append(f"- Generated at: `{datetime_now_str()}`")
    lines.append("")
    for strat, d in strat_dirs.items():
        rel = d.relative_to(report_md_path.parent)
        lines.append(f"### {strat}")
        lines.append(f"- Summary CSV: `{rel / 'hold_ev_summary.csv'}`")
        lines.append(f"- Plots: `{rel / 'hold_ev.png'}`, `{rel / 'hold_ev_cum_mean.png'}`, `{rel / 'hold_winrate.png'}`, `{rel / 'hold_profit_factor.png'}`")
        lines.append("")

    report_md_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def datetime_now_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
