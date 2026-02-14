import pandas as pd
import numpy as np

# Load Trades
try:
    df = pd.read_csv("C:/garam/garam/results/simulation/5months_phase7/trades_5months_phase7.csv")
    if df.empty:
        print("No trades found.")
        exit()
        
    # Calculate Metrics
    initial_capital = 10_000_000
    df['equity'] = initial_capital + df['net_pnl'].cumsum()
    
    # MDD
    peak = df['equity'].cummax()
    drawdown = (df['equity'] - peak) / peak
    mdd = drawdown.min()
    
    # Return
    final_equity = df['equity'].iloc[-1]
    ret = (final_equity / initial_capital) - 1.0
    
    # Trade Stats
    win_trades = df[df['net_pnl'] > 0]
    loss_trades = df[df['net_pnl'] <= 0]
    win_rate = len(win_trades) / len(df)
    
    print(f"=== Phase 7 V2 Metrics ===")
    print(f"Return: {ret*100:.2f}%")
    print(f"MDD: {mdd*100:.2f}%")
    print(f"Trades: {len(df)}")
    print(f"Win Rate: {win_rate*100:.1f}%")
    print(f"Final Equity: {final_equity:,.0f}")
    
except Exception as e:
    print(f"Error: {e}")
