import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS

def load_results(strategy_name):
    results_dir = PATHS.BASE_DIR / "results" / strategy_name
    trades_file = results_dir / "trades.csv"
    equity_file = results_dir / "equity.csv" # Wait, did I save equity.csv?
    
    if not trades_file.exists():
        print(f"Warning: Trades file not found for {strategy_name}")
        return None, None
        
    trades = pd.read_csv(trades_file)
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    trades.sort_values('exit_time', inplace=True)
    
    # Reconstruct Equity Curve
    initial_capital = 100_000_000
    trades['cumulative_pnl'] = trades['pnl'].cumsum()
    trades['equity'] = initial_capital + trades['cumulative_pnl']
    
    # Create daily equity series (resample)
    equity = trades.set_index('exit_time')[['equity']].resample('D').last().ffill()
    # Fill start
    if not equity.empty:
        start_date = equity.index[0] - pd.Timedelta(days=1)
        equity = pd.concat([pd.DataFrame({'equity': [initial_capital]}, index=[start_date]), equity])
    
    return trades, equity

def calculate_metrics(trades, equity):
    if trades is None or trades.empty:
        return {
            "Total PnL": 0.0,
            "Win Rate": 0.0,
            "Trade Count": 0,
            "Max DD": 0.0,
            "CAGR": 0.0
        }
        
    total_pnl = trades['pnl'].sum()
    win_rate = (trades['pnl'] > 0).mean() * 100
    trade_count = len(trades)
    
    # Max DD
    equity_curve = equity['equity']
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    max_dd = drawdown.min() * 100
    
    # CAGR (Approximate for 2 months)
    # Assuming 100M start
    start_equity = 100_000_000
    end_equity = equity_curve.iloc[-1]
    total_return = (end_equity - start_equity) / start_equity
    days = (equity.index[-1] - equity.index[0]).days
    if days > 0:
        cagr = ((1 + total_return) ** (365 / days) - 1) * 100
    else:
        cagr = 0.0
        
    return {
        "Total PnL": total_pnl,
        "Win Rate": win_rate,
        "Trade Count": trade_count,
        "Max DD": max_dd,
        "CAGR": cagr
    }

def main():
    strategies = ["Pure_v2", "Pure_v3", "Hybrid_v2_Attack"]
    metrics_list = []
    
    for strategy in strategies:
        print(f"Analyzing {strategy}...")
        trades, equity = load_results(strategy)
        metrics = calculate_metrics(trades, equity)
        metrics['Strategy'] = strategy
        metrics_list.append(metrics)
        
    df_metrics = pd.DataFrame(metrics_list).set_index('Strategy')
    print("\n=== Performance Comparison ===")
    print(df_metrics)
    
    # Success Criteria Check
    hybrid = df_metrics.loc['Hybrid_v2_Attack']
    pure_v2 = df_metrics.loc['Pure_v2']
    pure_v3 = df_metrics.loc['Pure_v3']
    
    best_pure_pnl = max(pure_v2['Total PnL'], pure_v3['Total PnL'])
    
    print("\n=== Success Criteria Check ===")
    print(f"Hybrid PnL: {hybrid['Total PnL']:,.0f}")
    print(f"Best Pure PnL: {best_pure_pnl:,.0f}")
    
    if hybrid['Total PnL'] > best_pure_pnl * 1.05:
        print("[PASS] Hybrid PnL > 105% of Best Pure")
    else:
        print("[FAIL] Hybrid PnL <= 105% of Best Pure")
        
    if hybrid['CAGR'] >= 20:
        print(f"[PASS] Hybrid CAGR ({hybrid['CAGR']:.1f}%) >= 20%")
    else:
        print(f"[FAIL] Hybrid CAGR ({hybrid['CAGR']:.1f}%) < 20%")

if __name__ == "__main__":
    main()
