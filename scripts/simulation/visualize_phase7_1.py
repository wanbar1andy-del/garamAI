import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def analyze_phase7_1(tag=""):
    # Load Data
    dir_name = "5months_phase7_1_k2.2" # Default Exp 1
    if tag: dir_name = f"5months_phase7_1_{tag}"
    
    sim_path = project_root / "results" / "simulation" / dir_name / "trades_phase7_1.csv"
    if not sim_path.exists():
        print(f"Simulation file not found: {sim_path}")
        return

    df = pd.read_csv(sim_path)
    if df.empty:
        print("No trades found.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    initial_cap = 10_000_000.0
    df['cum_pnl'] = df['net_pnl'].cumsum()
    df['equity'] = initial_cap + df['cum_pnl']
    df['return'] = (df['equity'] / initial_cap) - 1.0
    
    # Metrics
    final_ret = df['return'].iloc[-1]
    peak = df['equity'].cummax()
    dd = (df['equity'] - peak) / peak
    mdd = dd.min()
    
    print(f"\n[Phase 7.1 ({dir_name}) Report]")
    print(f"Final Return: {final_ret*100:.2f}%")
    print(f"MDD:          {mdd*100:.2f}%")
    print(f"Total Trades: {len(df)}")
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'], df['return']*100, label=f"Phase 7.1 ({tag})", color="blue")
    
    max_idx = df['return'].idxmax()
    plt.scatter(df.loc[max_idx, 'time'], df.loc[max_idx, 'return']*100, color='green', marker='^')
    
    plt.title(f"Phase 7.1 ({tag}) | Return: {final_ret*100:.2f}% | MDD: {mdd*100:.2f}%")
    plt.ylabel("Return (%)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axhline(0, color='black')
    plt.legend()
    
    out_path = project_root / "results" / "simulation" / f"equity_phase7_1_{tag}.png"
    plt.savefig(out_path)
    print(f"Saved Chart: {out_path}")

if __name__ == "__main__":
    analyze_phase7_1("k2.2")
