"""
Turbo Performance Metrics Verification (SSOT)

Purpose: Calculate verified performance metrics from equity curve.
This is the SINGLE SOURCE OF TRUTH for turbo performance claims.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


def calculate_metrics(equity: pd.Series, rf_annual: float = 0.03) -> dict:
    """
    Calculate performance metrics from equity curve.
    
    Args:
        equity: Daily equity values (index can be dates or integers)
        rf_annual: Annual risk-free rate (default: 3%)
    
    Returns:
        Dictionary with verified metrics
    """
    equity = equity.astype(float)
    
    # 1. Total Return
    total_ret = (equity.iloc[-1] / equity.iloc[0]) - 1.0
    
    # 2. Maximum Drawdown
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    mdd = float(drawdown.min())
    mdd_idx = drawdown.idxmin()
    peak_before_mdd = running_max.loc[:mdd_idx].idxmax()
    
    # 3. Daily Returns
    daily_ret = equity.pct_change().dropna()
    
    # 4. Sharpe Ratio (annualized, daily data)
    rf_daily = rf_annual / 252
    excess_return = daily_ret - rf_daily
    sharpe_daily = excess_return.mean() / daily_ret.std(ddof=1)
    sharpe_annual = sharpe_daily * np.sqrt(252)
    
    # 5. Win Rate (daily)
    win_rate = (daily_ret > 0).sum() / len(daily_ret)
    
    # 6. Calmar Ratio (return / abs(mdd))
    calmar = total_ret / abs(mdd) if mdd != 0 else np.nan
    
    # 7. Sortino Ratio (annualized)
    downside_ret = daily_ret[daily_ret < 0]
    if len(downside_ret) > 0:
        downside_std = downside_ret.std(ddof=1)
        sortino_daily = (daily_ret.mean() - rf_daily) / downside_std
        sortino_annual = sortino_daily * np.sqrt(252)
    else:
        sortino_annual = np.nan
    
    # 8. Volatility (annualized)
    volatility_annual = daily_ret.std(ddof=1) * np.sqrt(252)
    
    # 9. Average holding period (days between rebalances)
    # For now, just count trading days
    trading_days = len(daily_ret)
    
    return {
        "total_return_pct": float(total_ret * 100),
        "mdd_pct": float(mdd * 100),
        "sharpe_ratio": float(sharpe_annual),
        "sortino_ratio": float(sortino_annual),
        "calmar_ratio": float(calmar),
        "win_rate_pct": float(win_rate * 100),
        "volatility_annual_pct": float(volatility_annual * 100),
        "trading_days": int(trading_days),
        "peak_before_mdd": str(peak_before_mdd),
        "mdd_point": str(mdd_idx),
        "initial_equity": float(equity.iloc[0]),
        "final_equity": float(equity.iloc[-1]),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="Path to equity curve CSV")
    p.add_argument("--column", required=True, help="Equity column name (e.g., 'v2_2_equity')")
    p.add_argument("--rf", type=float, default=0.03, help="Annual risk-free rate")
    p.add_argument("--tolerance_return", type=float, default=0.002, help="Return tolerance (0.2%p)")
    p.add_argument("--tolerance_mdd", type=float, default=0.002, help="MDD tolerance (0.2%p)")
    p.add_argument("--tolerance_sharpe", type=float, default=0.5, help="Sharpe tolerance")
    p.add_argument("--expected_return", type=float, default=None, help="Expected return % for validation")
    p.add_argument("--expected_mdd", type=float, default=None, help="Expected MDD % for validation")
    p.add_argument("--expected_sharpe", type=float, default=None, help="Expected Sharpe for validation")
    p.add_argument("--out_json", default=None, help="Output JSON path for verified metrics")
    args = p.parse_args()
    
    # Load CSV
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    if args.column not in df.columns:
        raise ValueError(f"Column '{args.column}' not found. Available: {list(df.columns)}")
    
    equity = df[args.column]
    
    # Calculate metrics
    print(f"[Verification] Calculating metrics from: {csv_path}")
    print(f"[Verification] Column: {args.column}")
    print(f"[Verification] Rows: {len(equity)}")
    
    metrics = calculate_metrics(equity, rf_annual=args.rf)
    
    # Print results
    print("\n" + "="*60)
    print("VERIFIED TURBO PERFORMANCE METRICS (SSOT)")
    print("="*60)
    print(f"Total Return:      {metrics['total_return_pct']:.2f}%")
    print(f"Max Drawdown:      {metrics['mdd_pct']:.2f}%")
    print(f"Sharpe Ratio:      {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio:     {metrics['sortino_ratio']:.2f}")
    print(f"Calmar Ratio:      {metrics['calmar_ratio']:.2f}")
    print(f"Win Rate:          {metrics['win_rate_pct']:.2f}%")
    print(f"Volatility (Ann.): {metrics['volatility_annual_pct']:.2f}%")
    print(f"Trading Days:      {metrics['trading_days']}")
    print(f"Initial Equity:    {metrics['initial_equity']:,.0f}")
    print(f"Final Equity:      {metrics['final_equity']:,.0f}")
    print("="*60)
    
    # Validation against expected values
    if args.expected_return is not None or args.expected_mdd is not None or args.expected_sharpe is not None:
        print("\n[VALIDATION RESULTS]")
        passed = True
        
        if args.expected_return is not None:
            diff = abs(metrics['total_return_pct'] - args.expected_return)
            status = "✓ PASS" if diff <= args.tolerance_return * 100 else "✗ FAIL"
            print(f"Return:  Expected {args.expected_return:.2f}%, Got {metrics['total_return_pct']:.2f}%, Diff {diff:.2f}%p → {status}")
            if status == "✗ FAIL":
                passed = False
        
        if args.expected_mdd is not None:
            diff = abs(metrics['mdd_pct'] - args.expected_mdd)
            status = "✓ PASS" if diff <= args.tolerance_mdd * 100 else "✗ FAIL"
            print(f"MDD:     Expected {args.expected_mdd:.2f}%, Got {metrics['mdd_pct']:.2f}%, Diff {diff:.2f}%p → {status}")
            if status == "✗ FAIL":
                passed = False
        
        if args.expected_sharpe is not None:
            diff = abs(metrics['sharpe_ratio'] - args.expected_sharpe)
            status = "✓ PASS" if diff <= args.tolerance_sharpe else "✗ FAIL"
            print(f"Sharpe:  Expected {args.expected_sharpe:.2f}, Got {metrics['sharpe_ratio']:.2f}, Diff {diff:.2f} → {status}")
            if status == "✗ FAIL":
                passed = False
        
        if not passed:
            print("\n⚠️  VALIDATION FAILED: Reported metrics do not match verified calculations!")
            print("    Use verified metrics as SSOT, discard reported values.")
        else:
            print("\n✓ VALIDATION PASSED: Reported metrics are verified.")
    
    # Save to JSON if requested
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "verified_at": datetime.now().isoformat(),
            "source_csv": str(csv_path),
            "equity_column": args.column,
            "rf_annual": args.rf,
            "metrics": metrics,
            "validation": {
                "expected_return": args.expected_return,
                "expected_mdd": args.expected_mdd,
                "expected_sharpe": args.expected_sharpe,
            }
        }
        
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"\n[Saved] Verified metrics → {out_path}")


if __name__ == "__main__":
    main()
