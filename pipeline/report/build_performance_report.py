# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min()) if len(dd) else 0.0

def profit_factor(pnls: pd.Series) -> float:
    pos = pnls[pnls > 0].sum()
    neg = -pnls[pnls < 0].sum()
    if neg == 0:
        return float("inf") if pos > 0 else 0.0
    return float(pos / neg)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest_dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    bdir = Path(args.backtest_dir)
    equity_path = bdir / "equity_curve.csv"
    trades_path = bdir / "trades.csv"

    if not equity_path.exists():
        raise FileNotFoundError(f"missing: {equity_path}")
    if not trades_path.exists():
        raise FileNotFoundError(f"missing: {trades_path}")

    eq = pd.read_csv(equity_path)
    tr = pd.read_csv(trades_path)

    eq["equity"] = pd.to_numeric(eq["equity"], errors="coerce")
    eq = eq.dropna(subset=["equity"])
    if eq.empty:
        raise ValueError("equity_curve is empty")

    start_eq = float(eq["equity"].iloc[0])
    end_eq = float(eq["equity"].iloc[-1])
    total_return = (end_eq / start_eq - 1.0) if start_eq > 0 else 0.0
    mdd = max_drawdown(eq["equity"])

    # trades: some rows are entries, some are exits; PnL exists only on exit rows
    pnls = pd.to_numeric(tr.get("pnl", pd.Series(dtype=float)), errors="coerce").dropna()
    exit_rows = tr[tr.columns.intersection(["exit_ts","symbol","entry_px","exit_px","qty","pnl","return_pct","reason"])].copy()

    trade_count = int(len(pnls))
    win_rate = float((pnls > 0).mean()) if trade_count else 0.0
    avg_trade_return = float(pd.to_numeric(tr.get("return_pct", pd.Series(dtype=float)), errors="coerce").dropna().mean()) if trade_count else 0.0
    pf = profit_factor(pnls) if trade_count else 0.0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    md = []
    md.append("# Phase 26 Performance Report")
    md.append("")
    md.append("## Run Summary")
    md.append(f"- Backtest dir: `{bdir.as_posix()}`")
    md.append("")
    md.append("## KPI (Core)")
    md.append(f"- Total Return: **{total_return*100:.2f}%**")
    md.append(f"- Max Drawdown (MDD): **{mdd*100:.2f}%**")
    md.append(f"- Trade Count (closed): **{trade_count}**")
    md.append(f"- Win Rate: **{win_rate*100:.2f}%**")
    md.append(f"- Profit Factor: **{pf:.3f}**" if np.isfinite(pf) else "- Profit Factor: **INF**")
    md.append(f"- Avg Trade Return: **{avg_trade_return*100:.3f}%**")
    md.append("")
    md.append("## Notes")
    md.append("- Strategy MVP: Top-1 1-minute ROC rotation, single-position all-in.")
    md.append("- Fees: included at backtest time (`fee_bps`).")
    md.append("")
    md.append("## Artifacts")
    md.append(f"- equity curve: `{(bdir / 'equity_curve.csv').as_posix()}`")
    md.append(f"- trades: `{(bdir / 'trades.csv').as_posix()}`")
    md.append("")

    out_path.write_text("\n".join(md), encoding="utf-8")
    print("[OK] report generated:", out_path)

    # Optional: write an exit-trades CSV for easy reading
    if not exit_rows.empty:
        exit_rows.to_csv(out_path.parent / "trades_closed.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
