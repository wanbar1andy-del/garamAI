import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def analyze_month1():
    # Load Data
    sim_path = project_root / "results" / "simulation" / "month1_v2" / "trades_month1_policy_v2.csv"
    if not sim_path.exists():
        print("Simulation file not found")
        return

    df = pd.read_csv(sim_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    # Calculate Equity Curve
    # Reconstruct from trade logs
    # To get daily close equity, we need to process chronologically.
    
    # Simpler approach: Cumulative PnL + Initial Capital
    # Note: Trade log includes realized PnL.
    
    initial_cap = 10_000_000.0
    equity = [initial_cap]
    times = [df['time'].iloc[0]]
    
    current_eq = initial_cap
    
    # We want to plot equity at each trade? Or Daily?
    # Trade-by-trade is better for detailed view.
    
    for _, row in df.iterrows():
        # Update equity on realized trades (Sell) or Entry Fees
        # In run_policy_v2_month1.py:
        # Buy: net_pnl = -cost -> logic: Equity reduced by fee.
        # Sell: net_pnl = Realized PnL (including fees).
        # So summing 'net_pnl' gives cumulative Change in Equity.
        
        change = row['net_pnl']
        current_eq += change
        equity.append(current_eq)
        times.append(row['time'])
        
    df_eq = pd.DataFrame({"time": times, "equity": equity})
    df_eq['return'] = (df_eq['equity'] / initial_cap) - 1.0
    
    # Metrics
    final_ret = df_eq['return'].iloc[-1]
    peak = df_eq['equity'].cummax()
    dd = (df_eq['equity'] - peak) / peak
    mdd = dd.min()
    
    # Sharpe (approx daily)
    # Resample to daily
    df_eq['date'] = df_eq['time'].dt.date
    daily_eq = df_eq.groupby('date')['equity'].last()
    daily_ret = daily_eq.pct_change().dropna()
    sharpe = (daily_ret.mean() / daily_ret.std()) * (252**0.5) if daily_ret.std() > 0 else 0
    
    print(f"\n[Month-1 Performance Report]")
    print(f"Return: {final_ret*100:.2f}%")
    print(f"MDD:    {mdd*100:.2f}%")
    print(f"Sharpe: {sharpe:.2f}")
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df_eq['time'], df_eq['return']*100, label="Policy v2 (Multi-Slot)", color="blue")
    
    # Annotate Max/Min
    max_idx = df_eq['return'].idxmax()
    min_idx = df_eq['return'].idxmin()
    plt.scatter(df_eq.loc[max_idx, 'time'], df_eq.loc[max_idx, 'return']*100, color='green', marker='^')
    plt.scatter(df_eq.loc[min_idx, 'time'], df_eq.loc[min_idx, 'return']*100, color='red', marker='v')
    
    plt.title(f"Month-1 Replay (2025-12) | Return: {final_ret*100:.2f}% | MDD: {mdd*100:.2f}% | Sharpe: {sharpe:.2f}")
    plt.ylabel("Return (%)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axhline(0, color='black', linewidth=1)
    plt.legend()
    
    out_path = project_root / "results" / "simulation" / "month1_policy_v2_equity.png"
    plt.savefig(out_path)
    print(f"Saved Chart: {out_path}")

if __name__ == "__main__":
    analyze_month1()
