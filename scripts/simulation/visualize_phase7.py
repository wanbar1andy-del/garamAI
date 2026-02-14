import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def analyze_phase7():
    # Load Data
    sim_path = project_root / "results" / "simulation" / "5months_phase7" / "trades_5months_phase7.csv"
    if not sim_path.exists():
        print("Simulation file not found")
        return

    df = pd.read_csv(sim_path)
    if df.empty:
        print("No trades found.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    # Approx Equity Logic
    initial_cap = 10_000_000.0
    df['cum_pnl'] = df['net_pnl'].cumsum()
    df['equity'] = initial_cap + df['cum_pnl']
    df['return'] = (df['equity'] / initial_cap) - 1.0
    
    # Metrics
    final_ret = df['return'].iloc[-1]
    peak = df['equity'].cummax()
    dd = (df['equity'] - peak) / peak
    mdd = dd.min()
    
    # Monthly Stats
    df['month'] = df['time'].dt.to_period('M')
    monthly = df.groupby('month')['net_pnl'].sum()
    
    # Count Trades per Month
    monthly_count = df.groupby('month')['time'].count()
    
    print(f"\n[Phase 7 Performance Report]")
    print(f"Final Return: {final_ret*100:.2f}%")
    print(f"MDD:          {mdd*100:.2f}%")
    print(f"Total Trades: {len(df)}")
    print("\n[Monthly PnL]")
    print(monthly)
    print("\n[Monthly Trade Count]")
    print(monthly_count)
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'], df['return']*100, label="Phase 7 (Trend+Sniper)", color="blue")
    
    # Annotate
    max_idx = df['return'].idxmax()
    plt.scatter(df.loc[max_idx, 'time'], df.loc[max_idx, 'return']*100, color='green', marker='^')
    
    plt.title(f"Phase 7 (2025.08~12) | Return: {final_ret*100:.2f}% | MDD: {mdd*100:.2f}%")
    plt.ylabel("Return (%)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axhline(0, color='black')
    plt.legend()
    
    out_path = project_root / "results" / "simulation" / "5months_equity_phase7.png"
    plt.savefig(out_path)
    print(f"Saved Chart: {out_path}")

if __name__ == "__main__":
    analyze_phase7()
