import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def analyze_5months():
    # Load Data
    sim_path = project_root / "results" / "simulation" / "5months_real" / "trades_5months_real.csv"
    if not sim_path.exists():
        print("Simulation file not found")
        return

    df = pd.read_csv(sim_path)
    if df.empty:
        print("No trades found.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    # Calculate Equity Curve
    # The 'balance' column in trade log is the cash balance AFTER the trade.
    # Total Equity = Cash Balance + Market Value of Open Positions.
    # However, the trade log only records realized trades.
    # To construct a daily equity curve, we need to realize that 'balance' update only happens on Buy/Sell.
    # But for a continuous curve, we should ideally mark-to-market.
    # Given the complexity, we will plot Realized Equity (Cash + Cost Basis of Open).
    # Or simpler: Just plot the 'balance' at each trade assuming full reinvestment loop.
    # Better: Reconstruct "Total Account Value" at each trade time.
    
    # Let's reconstruct from Trade Log + Initial Capital logic.
    # Actually `run_policy_v2_5months_real.py` updates `self.capital` (Cash).
    # It does not log 'Equity'.
    # But on Sell, Capital increases. On Buy, Capital decreases.
    # So 'Cash Balance' is not 'Equity'.
    # We need to estimate Equity.
    # Equity ~ Cash + Sum(Qty * EntryPrice) (Ignoring unrealized PnL for simplicity or assuming short holding periond).
    # Since we trade intraday/frequently, Realized Equity Curve is close enough.
    
    # Let's approximate Equity at each trade point:
    # We know cash 'balance'. We can track 'invested amount'.
    
    invested = 0.0
    equity_curve = []
    times = []
    
    # Iterate trades to track invested capital
    # We need to process strictly chronologically.
    
    # Initial
    initial_cap = 10_000_000.0
    current_cash = initial_cap
    
    for _, row in df.iterrows():
        # Update State
        side = row['side']
        qty = row['qty']
        price = row['price']
        cost_val = qty * price
        
        # 'balance' in CSV is Cash Balance. Use valid source if available.
        if 'balance' in row:
             current_cash = row['balance']
        
        if side == 'BUY':
             invested += cost_val # Approx Entry Value
        elif side == 'SELL':
             # We assume FIFO or specific lot matching?
             # Simulator uses avg cost or specific lot.
             # If we just track total invested cost basis:
             invested -= (cost_val) # Removing cost basis? 
             # No, sell price includes profit.
             # Invested amount (Cost Basis) reduces by the Cost Basis of sold items.
             # We don't have cost basis in log explicitly for the sold part!
             # Wait, `net_pnl` is available.
             # Net PnL = (Gross - Cost).
             # We can just sum Net PnL to Initial Capital to get Realized Equity.
             pass
             
    # Simpler Method: Cumulative PnL + Initial Capital = Realized Equity.
    # This ignores unrealized PnL of open positions, but at the end of 5 months everything is likely closed or small.
    # And specifically for 'Compounding' view, Realized Equity is what matters for re-betting.
    
    df['cum_pnl'] = df['net_pnl'].cumsum()
    df['equity'] = initial_cap + df['cum_pnl']
    df['return'] = (df['equity'] / initial_cap) - 1.0
    
    # Metrics
    final_ret = df['return'].iloc[-1]
    peak = df['equity'].cummax()
    dd = (df['equity'] - peak) / peak
    mdd = dd.min()
    
    # Year/Month Stats
    df['month'] = df['time'].dt.to_period('M')
    monthly = df.groupby('month')['net_pnl'].sum()
    monthly_ret = monthly / initial_cap # Approx return contribution
    
    print(f"\n[5-Month Performance Report]")
    print(f"Final Return: {final_ret*100:.2f}%")
    print(f"MDD:          {mdd*100:.2f}%")
    print(f"Total Trades: {len(df)}")
    print("\n[Monthly PnL]")
    print(monthly)
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'], df['return']*100, label="Policy v2 (Real 5M)", color="blue")
    
    # Annotations
    max_idx = df['return'].idxmax()
    plt.scatter(df.loc[max_idx, 'time'], df.loc[max_idx, 'return']*100, color='green', marker='^')
    
    plt.title(f"5-Month Unbiased Replay (2025.08~12) | Return: {final_ret*100:.2f}% | MDD: {mdd*100:.2f}%")
    plt.ylabel("Return (%)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axhline(0, color='black')
    plt.legend()
    
    out_path = project_root / "results" / "simulation" / "5months_equity_real.png"
    plt.savefig(out_path)
    print(f"Saved Chart: {out_path}")

if __name__ == "__main__":
    analyze_5months()
