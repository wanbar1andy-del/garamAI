import pickle
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.research.regime.miracle_engine import Trade

def analyze_wfo(path):
    print(f"Loading WFO results from {path}...")
    with open(path, 'rb') as f:
        data = pickle.load(f)
        
    trades = data.get('trades', [])
    wfo_summary = data.get('wfo_summary', [])
    
    print(f"Total Trades: {len(trades)}")
    
    if not trades:
        print("No trades to analyze.")
        return

    # 1. Equity Curve
    df_trades = pd.DataFrame([t.__dict__ for t in trades])
    df_trades['timestamp'] = pd.to_datetime(df_trades['exit_time'])
    df_trades = df_trades.sort_values('timestamp')
    
    df_trades['equity_curve'] = (1 + df_trades['pnl_pct']).cumprod()
    
    print("\nPerformance Metrics:")
    start_date = df_trades['timestamp'].iloc[0]
    end_date = df_trades['timestamp'].iloc[-1]
    years = (end_date - start_date).days / 365.25 # Use 365.25 for better accuracy
    
    print(f"Trade Period: {start_date.date()} ~ {end_date.date()} ({years:.2f} years)")
    
    total_return = df_trades['equity_curve'].iloc[-1] - 1
    cagr = (1 + total_return) ** (1 / years) - 1
    
    # Max DD
    peak = df_trades['equity_curve'].cummax()
    dd = (peak - df_trades['equity_curve']) / peak
    max_dd = dd.max()
    
    print(f"Total Return: {total_return:.2%}")
    print(f"CAGR: {cagr:.2%}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print(f"Win Rate: {len(df_trades[df_trades['pnl_pct'] > 0]) / len(df_trades):.2%}")
    
    # 2. Parameter Stability
    print("\nParameter Stability:")
    params_df = pd.DataFrame([s['best_params'] for s in wfo_summary if s['best_params']])
    
    for col in params_df.columns:
        print(f"\n{col}:")
        print(params_df[col].value_counts(normalize=True).head(3))

if __name__ == "__main__":
    analyze_wfo("c:/garam/garam/data/wfo_results.pkl")
