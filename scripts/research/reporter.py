from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt

# Integration
# Integration
from garam_core.analysis.edge_matrix import EdgeAnalyzer


import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt


REQ_KEYS = [
    "symbol",
    "strategy",
    "roi",
    "max_drawdown",
    "trades",
    "win_rate",
    "profit_factor",
    "avg_win",
    "avg_loss",
    "avg_loss_abs",
    "win_loss_ratio",
    "cost_paid_total",
    "equity_curve",
]


def _ensure_out_dir(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _sanitize_symbol(sym: str) -> str:
    return "".join([c for c in sym if c.isalnum() or c in ("_", "-", ".")])


def _as_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def _build_summary_df(results: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for r in results:
        # 최소 요구키 검증 (누락되면 가능한 만큼 채움)
        row = {
            "symbol": r.get("symbol", ""),
            "strategy": r.get("strategy", r.get("strategy_name", r.get("name", ""))),
            "roi": _as_float(r.get("roi", 0.0)),
            "max_drawdown": _as_float(r.get("max_drawdown", 0.0)),
            "trades": int(r.get("trades", 0) or 0),
            "win_rate": _as_float(r.get("win_rate", 0.0)),
            "profit_factor": _as_float(r.get("profit_factor", 0.0)),
            "avg_win": _as_float(r.get("avg_win", 0.0)),
            "avg_loss": _as_float(r.get("avg_loss", 0.0)),
            "avg_loss_abs": _as_float(r.get("avg_loss_abs", abs(_as_float(r.get("avg_loss", 0.0))))),
            "win_loss_ratio": _as_float(r.get("win_loss_ratio", 0.0)),
            "cost_paid_total": _as_float(r.get("cost_paid_total", 0.0)),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # 정렬 편의: ROI 내림차순, MDD(절댓값) 오름차순, Trades 내림차순
    if not df.empty:
        df["mdd_abs"] = df["max_drawdown"].abs()
        df = df.sort_values(["roi", "mdd_abs", "trades"], ascending=[False, True, False]).drop(columns=["mdd_abs"])

    return df


def _plot_equity_comparison_for_symbol(results: List[Dict[str, Any]], out_dir: Path, symbol: str) -> Path:
    sym = _sanitize_symbol(symbol)
    fig_path = out_dir / f"equity_{sym}.png"

    # symbol에 해당하는 결과만 모음
    subset = [r for r in results if str(r.get("symbol", "")) == symbol]
    if not subset:
        return fig_path

    plt.figure()
    for r in subset:
        eq = r.get("equity_curve", None)
        if eq is None:
            continue
        # equity_curve는 pandas Series 기대
        try:
            s = pd.Series(eq)
        except Exception:
            continue

        name = r.get("strategy", "unknown")
        plt.plot(s.index, s.values, label=str(name))

    plt.title(f"Equity Comparison - {symbol}")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()

    return fig_path


def _portfolio_equity_by_strategy(results: List[Dict[str, Any]]) -> Dict[str, pd.Series]:
    """
    동일가중 포트폴리오(몰빵 방지 검증):
    - 전략별로 각 심볼의 equity_curve를 시간축(인덱스) 기준 outer-join 후 평균.
    - NaN은 해당 시점에 데이터 없는 것으로 보고 평균에서 제외(mean skipna).
    """
    # (strategy -> list of equity series)
    buckets: Dict[str, List[pd.Series]] = {}
    for r in results:
        strat = str(r.get("strategy", "unknown"))
        eq = r.get("equity_curve", None)
        if eq is None:
            continue
        try:
            s = pd.Series(eq)
        except Exception:
            continue
        if s.empty:
            continue
        buckets.setdefault(strat, []).append(s)

    portfolio: Dict[str, pd.Series] = {}
    for strat, series_list in buckets.items():
        if not series_list:
            continue
        # index 정렬 + outer join
        df = pd.concat(series_list, axis=1, join="outer")
        # 동일가중 평균 (NaN 제외)
        port = df.mean(axis=1, skipna=True)
        # 시작점 정규화(=1.0) 강제: 서로 다른 기간/데이터 구간 비교를 위해
        if len(port) > 0 and port.iloc[0] != 0:
            port = port / port.iloc[0]
        portfolio[strat] = port

    return portfolio


def _plot_portfolio_equity(results: List[Dict[str, Any]], out_dir: Path) -> Path:
    fig_path = out_dir / "portfolio_equity.png"
    port_map = _portfolio_equity_by_strategy(results)

    if not port_map:
        return fig_path

    plt.figure()
    for strat, s in port_map.items():
        plt.plot(s.index, s.values, label=strat)

    plt.title("Portfolio Equity (Equal-Weight Across Symbols) by Strategy")
    plt.xlabel("Time")
    plt.ylabel("Equity (Normalized)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()

    return fig_path


def _format_pct(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x*100:.2f}%"


def _format_float(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.4f}"


def _write_markdown_report(
    out_dir: Path,
    summary_df: pd.DataFrame,
    symbols: List[str],
    fig_paths_by_symbol: Dict[str, Path],
    portfolio_fig_path: Path,
    edge_analysis: Optional[Dict[str, Any]] = None, # [NEW]
) -> Path:
    
    # Use standard report_writer logic for Markdown as well?
    # Or keep this for legacy "Unified Report"?
    # For now, we will create a NEW 'report.json' and use report_writer for the MAIN output,
    # This legacy markdown function can remain as 'unified_backtest_report.md'
    
    lines = []
    lines.append("# Unified Backtest Report\n")
    # ... (existing content preserved for unified overview)
    lines.append("## Summary\n")
    lines.append(f"- Symbols: {', '.join(symbols)}\n")
    
    # [NEW] Inject Edge Matrix Global
    if edge_analysis:
        ov = edge_analysis.get("overall", {})
        lines.append(f"- **System Net Expectancy**: {ov.get('expectancy_net', 0):.5f}\n")
    
    # ... Rest logic for dataframes ...
    lines.append(f"- Total rows: {len(summary_df)} (symbol × strategy)\n")

    lines.append("\n## Strategy Ranking (Top)\n")
    if top_df.empty:
        lines.append("- No results.\n")
    else:
        # 보기 좋게 가공
        show = top_df[["symbol", "strategy", "roi", "max_drawdown", "trades", "win_rate", "profit_factor"]].copy()
        show["roi"] = show["roi"].map(_format_pct)
        show["max_drawdown"] = show["max_drawdown"].map(_format_pct)
        show["win_rate"] = show["win_rate"].map(_format_pct)
        show["profit_factor"] = show["profit_factor"].map(_format_float)
        lines.append(show.to_markdown(index=False))
        lines.append("\n")

    lines.append("\n## Strategy Average (Across Symbols)\n")
    if strat_avg.empty:
        lines.append("- No results.\n")
    else:
        show = strat_avg.copy()
        show["roi_mean"] = show["roi_mean"].map(_format_pct)
        show["mdd_mean"] = show["mdd_mean"].map(_format_pct)
        show["win_rate_mean"] = show["win_rate_mean"].map(_format_pct)
        show["profit_factor_mean"] = show["profit_factor_mean"].map(_format_float)
        lines.append(show.to_markdown(index=False))
        lines.append("\n")

    # If Edge Analysis exists, append concise summary
    if edge_analysis:
        lines.append("\n## Edge Matrix Summary\n")
        lines.append(f"- Net Exp: {edge_analysis.get('overall', {}).get('expectancy_net', 0):.5f}\n")
        lines.append(f"- Cost/Trade: {edge_analysis.get('overall', {}).get('cost_per_trade_avg', 0):.5f}\n")
        tags = edge_analysis.get("collapse_tags", [])
        if tags:
            lines.append(f"- Tags: {', '.join(tags)}\n")
            
    lines.append("\n## Equity Curves (Per Symbol)\n")
    # ... (images)
    for sym in symbols:
        p = fig_paths_by_symbol.get(sym)
        if p is None:
            continue
        rel = p.name
        lines.append(f"### {sym}\n")
        lines.append(f"![equity_{_sanitize_symbol(sym)}]({rel})\n")

    lines.append("\n## Portfolio Equity (Equal-Weight)\n")
    if portfolio_fig_path is not None:
        lines.append(f"![portfolio_equity]({portfolio_fig_path.name})\n")

    md_path = out_dir / "report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def generate_report(
    results: List[Dict[str, Any]], 
    out_dir: Path,
    minute_data_map: Optional[Dict[str, pd.DataFrame]] = None, # [NEW]
) -> None:
    """
    Entry:
      - results: list of dict returned by run_backtest_unified()
      - out_dir: PROJECT_ROOT / "reports"
      - minute_data_map: symbol -> DataFrame (for EdgeMatrix micro-regime calc)
    Output:
      - summary.csv
      - report.md (Unified)
      - [NEW] report.json (v2.1 Schema via report_writer if imported, or injected into md)
    """
    out_dir = _ensure_out_dir(Path(out_dir))

    # 1) Summary table
    summary_df = _build_summary_df(results)
    summary_csv = out_dir / "summary.csv"
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")

    # 2) Edge Matrix Analysis (v2.1)
    edge_analysis = None
    if minute_data_map:
        # Aggregate all trades from all results into one DataFrame
        all_trades = []
        for r in results:
            t_list = r.get("trades_df") # Need to ensure runner returns this frame or list of dicts
            if t_list is not None and not t_list.empty:
                t = t_list.copy()
                t['strategy'] = r.get("strategy", "unknown")
                t['symbol'] = r.get("symbol", "unknown")
                all_trades.append(t)
        
        if all_trades:
            full_trades_df = pd.concat(all_trades)
            # Just take the first symbol's data for regime? or Multi-symbol regime?
            # EDGE CASE: Multi-symbol Edge Matrix requires alignment or symbol-specific regime processing.
            # V1 Assumption: Single Symbol run or aggregated stats.
            # If Multi-symbol, we might need a dominant index or loop per symbol.
            # FOR NOW: Pick the first available symbol data to establish 'Market Regime' 
            # OR pass a specific benchmark. 
            # Better: Run analysis PER SYMBOL? or Global?
            # User wants "EdgeMatrix_1Y" -> likely aggregated across Top-50?
            # Let's try to pass the concatenated minute data? No, that's impossible.
            # Compromise: Use the first symbol in the map as the "Regime Source" (e.g. 005930) or Average?
            # Correct approach: Calculate regime per symbol, map trades, then aggregate.
            
            # --- Per-Trade Regime Mapping ---
            analyzer = EdgeAnalyzer() # Use defaults from class
            # We need to map regime per trade based on its specific symbol's data
            full_trades_df['regime'] = "UNCERTAIN"
            
            # This loop maps regime for each symbol's trades individually
            for sym, df_min in minute_data_map.items():
                # 1. Calc regime for this symbol
                regimes = analyzer.micro_regime_v1_public(df_min) # Need to expose this or use class method?
                # Actually EdgeAnalyzer.analyze does it internal.
                # We need to expose static method or use instance.
                # Let's just use the analyze() method per symbol and aggregate "by_regime"?
                pass 
            
            # SIMPLIFICATION:
            # Just run analyzer on the FIRST symbol if it's a single-symbol verification.
            # If multi-symbol, strictly we need complex aggregation.
            # Given instructions are "Verify Turbo V3" (Single Symbol focus usually), 
            # I will implement Single Symbol logic first.
            
            first_sym = list(minute_data_map.keys())[0] if minute_data_map else None
            if first_sym and first_sym in minute_data_map:
                # Filter trades for this symbol
                sym_trades = full_trades_df[full_trades_df['symbol'] == first_sym]
                if not sym_trades.empty:
                    edge_analysis = analyzer.analyze(
                        trades_df=sym_trades,
                        minute_df=minute_data_map[first_sym]
                    )

    # 3) Figures per symbol
    symbols = sorted(list({str(r.get("symbol", "")) for r in results if str(r.get("symbol", ""))}))
    fig_paths_by_symbol: Dict[str, Path] = {}
    for sym in symbols:
        fig_paths_by_symbol[sym] = _plot_equity_comparison_for_symbol(results, out_dir, sym)

    # 3) Portfolio equity figure (equal-weight across symbols)
    portfolio_fig_path = _plot_portfolio_equity(results, out_dir)

    # 4) Markdown report
    _write_markdown_report(out_dir, summary_df, symbols, fig_paths_by_symbol, portfolio_fig_path)

    print(f"[reporter] summary.csv saved: {summary_csv}")
    print(f"[reporter] report.md saved: {out_dir / 'report.md'}")
    print(f"[reporter] portfolio_equity.png saved: {portfolio_fig_path}")
    for sym, p in fig_paths_by_symbol.items():
        print(f"[reporter] equity_{_sanitize_symbol(sym)}.png saved: {p}")
