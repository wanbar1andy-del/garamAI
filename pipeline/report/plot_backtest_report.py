# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min()) if len(dd) else 0.0

def parse_ts(ts: str):
    # Try generic pandas parsing first
    return pd.to_datetime(ts, errors='coerce')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest_dir", required=True)
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    bdir = Path(args.backtest_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    eq_path = bdir / "equity_curve.csv"
    tr_path = bdir / "trades.csv"
    
    # Defaults
    total_return = 0.0
    mdd = 0.0
    year_months = []
    monthly_rets = []
    trade_count = 0
    win_rate = 0.0

    # 1. Equity Processing
    if eq_path.exists():
        eq = pd.read_csv(eq_path)
        # Normalize
        eq.columns = [c.lower() for c in eq.columns]
        
        if "equity" in eq.columns:
            eq["equity"] = pd.to_numeric(eq["equity"], errors="coerce")
            eq = eq.dropna(subset=["equity"])
            
            if eq.empty:
                print(f"[Warn] Equity data empty after filtering: {path}")
                return
            
            # Timestamp
            if "ts" in eq.columns:
                eq["dt"] = eq["ts"].apply(parse_ts)
            else:
                eq["dt"] = pd.RangeIndex(len(eq))
            eq = eq.dropna(subset=["dt"])
            eq = eq.sort_values("dt")
            
            if len(eq) > 1:
                start_eq = float(eq["equity"].iloc[0])
                if start_eq > 0:
                    eq["cumret"] = eq["equity"] / start_eq - 1.0
                    eq["peak"] = eq["equity"].cummax()
                    eq["dd"] = eq["equity"] / eq["peak"] - 1.0
                    
                    total_return = float(eq["cumret"].iloc[-1])
                    mdd = max_drawdown(eq["equity"])
                    
                    # Plot Equity
                    plt.figure(figsize=(10, 6))
                    plt.plot(eq["dt"], eq["cumret"]*100, label="Strategy")
                    plt.title("Equity Curve (%)")
                    plt.ylabel("Return (%)")
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                    plt.savefig(out_dir / "equity_curve.png")
                    plt.close()
                    
                    # Plot Drawdown
                    plt.figure(figsize=(10, 4))
                    plt.fill_between(eq["dt"], eq["dd"]*100, 0, color='red', alpha=0.3)
                    plt.title("Drawdown (%)")
                    plt.ylabel("DD (%)")
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                    plt.savefig(out_dir / "drawdown.png")
                    plt.close()
                    
                    # Monthly Returns
                    # Resample to Daily Last, then Monthly
                    eq["day"] = eq["dt"].dt.to_period("D")
                    daily = eq.groupby("day")["equity"].last()
                    if not daily.empty:
                        # Monthly calc
                        daily.index = daily.index.to_timestamp()
                        m_ends = daily.resample("ME").last()
                        m_rets_s = m_ends.pct_change().fillna(0.0)
                        # Fix first month: (End / Start) - 1
                        # If meaningful start date exists
                        
                        year_months = m_rets_s.index.strftime("%Y-%m").tolist()
                        monthly_rets = (m_rets_s * 100).round(2).tolist()
                        
                        plt.figure(figsize=(10, 5))
                        plt.bar(year_months, monthly_rets, color=['red' if v < 0 else 'blue' for v in monthly_rets])
                        plt.title("Monthly Returns (%)")
                        plt.xticks(rotation=45)
                        plt.grid(True, alpha=0.3, axis='y')
                        plt.tight_layout()
                        plt.savefig(out_dir / "monthly_returns.png")
                        plt.close()

    # 2. Trade Processing
    if tr_path.exists():
        tr = pd.read_csv(tr_path)
        tr.columns = [c.lower() for c in tr.columns]
        
        if not tr.empty:
            trade_count = len(tr)
            if "pnl" in tr.columns:
                 wins = tr[tr["pnl"] > 0]
                 win_rate = len(wins) / trade_count
            
            if "return_pct" in tr.columns:
                 plt.figure(figsize=(10, 5))
                 plt.hist(tr["return_pct"] * 100, bins=50, alpha=0.7)
                 plt.title("Trade Return Distribution (%)")
                 plt.grid(True, alpha=0.3)
                 plt.tight_layout()
                 plt.savefig(out_dir / "trade_return_hist.png")
                 plt.close()

    # Summary JSON
    summary = {
        "total_return_pct": round(total_return * 100, 2),
        "mdd_pct": round(mdd * 100, 2),
        "trade_count_closed": trade_count,
        "win_rate_pct": round(win_rate * 100, 2),
        "months": year_months,
        "monthly_return_pct": monthly_rets,
    }
    
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print("[OK] charts saved to:", out_dir)

if __name__ == "__main__":
    main()
