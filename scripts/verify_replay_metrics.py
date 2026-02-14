"""
Verify Replay Metrics (SSOT)

Calculates standard performance metrics from equity curve CSV.
Input: equity_curve.csv (Date, NetReturn)
Output: metrics_verified.json

Metrics:
- Return (Total, Annualized)
- MDD
- Sharpe
- Calmar
- Sortino
- Win Rate
"""
from __future__ import annotations

import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path

def calculate_metrics(equity_csv: Path, risk_free_rate: float = 0.03):
    print(f"Loading equity curve: {equity_csv}")
    
    # Load equity curve
    # Expects columns: date, equity or date, net_ret
    try:
        df = pd.read_csv(equity_csv)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None
        
    df.columns = [c.lower() for c in df.columns]
    
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
    
    # Determine returns
    if "net_ret" in df.columns:
        daily_ret = df["net_ret"]
        equity = (1 + daily_ret).cumprod()
    elif "equity" in df.columns:
        equity = df["equity"]
        daily_ret = equity.pct_change().fillna(0)
    else:
        print("CSV must have 'net_ret' or 'equity' column")
        return None
        
    # 1. Total Return
    total_ret = (equity.iloc[-1] / equity.iloc[0]) - 1.0
    
    # 2. Annualized Return (assuming 252 trading days)
    days = (df.index[-1] - df.index[0]).days
    years = max(days / 365.25, 0.001) # Avoid div by zero
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1/years) - 1.0
    
    cagr_warning = False
    if days < 90:
        cagr_warning = True
        # print("Warning: Period < 90 days, annualized metrics (CAGR, Sharpe, Calmar) may be unreliable.")
    
    # 3. MDD
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    mdd = drawdown.min()
    
    # 4. Volatility (Annualized)
    vol = daily_ret.std() * np.sqrt(252)
    
    # 5. Sharpe Ratio
    # Excess return over RF
    excess_ret = daily_ret.mean() * 252 - risk_free_rate
    sharpe = excess_ret / vol if vol > 0 else 0.0
    
    # 6. Sortino Ratio
    # Downside volatility
    downside_ret = daily_ret[daily_ret < 0]
    downside_vol = downside_ret.std() * np.sqrt(252)
    sortino = excess_ret / downside_vol if downside_vol > 0 else 0.0
    
    # 7. Calmar Ratio
    calmar = cagr / abs(mdd) if mdd < 0 else 0.0
    
    # 8. Win Rate (Daily)
    win_days = (daily_ret > 0).sum()
    n_daily_returns = len(daily_ret)
    win_rate_daily = win_days / n_daily_returns if n_daily_returns > 0 else 0.0
    
    # 9. Period Return / MDD
    period_return_over_mdd = total_ret / abs(mdd) if mdd != 0 else 0.0
    
    metrics = {
        "period_days": int(days),
        "n_equity_points": int(len(equity)),
        "n_daily_returns": int(n_daily_returns),
        "total_return_pct": float(total_ret * 100),
        "cagr": float(cagr),
        "cagr_reliability": "low_period_short" if cagr_warning else "normal",
        "mdd_pct": float(mdd * 100),
        "period_return_over_mdd": float(period_return_over_mdd),
        "volatility_annualized": float(vol),
        "sharpe_annualized": float(sharpe),
        "sortino": float(sortino),
        "calmar": float(calmar),
        "win_rate_daily": float(win_rate_daily),
        "risk_free_rate": risk_free_rate
    }
    
    return metrics

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--equity", required=True, help="Path to equity_curve.csv")
    p.add_argument("--rf_annual", type=float, default=0.03, help="Risk free rate")
    p.add_argument("--out", required=True, help="Output JSON path")
    args = p.parse_args()
    
    metrics = calculate_metrics(Path(args.equity), args.rf_annual)
    
    if metrics:
        with open(args.out, "w") as f:
            json.dump(metrics, f, indent=2)
        print(json.dumps(metrics, indent=2))
        print(f"[OK] Verified metrics saved to {args.out}")
    else:
        print("[FAIL] Could not calculate metrics")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
