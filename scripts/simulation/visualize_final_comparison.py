import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def load_equity(path, name):
    if not path.exists():
        print(f"File not found: {path}")
        return None
    
    df = pd.read_csv(path)
    if df.empty: return None
    
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    initial_cap = 10_000_000.0
    df['cum_pnl'] = df['net_pnl'].cumsum()
    df['equity'] = initial_cap + df['cum_pnl']
    df['return'] = (df['equity'] / initial_cap) - 1.0
    
    # Resample to Daily for smoother plot? Or keep intraday.
    # Keep intraday 'time' points
    return df[['time', 'return']]

def main():
    sim_dir = project_root / "results" / "simulation"
    
    scenarios = [
        ("Phase 6 (Fail)", sim_dir / "5months_real" / "trades_5months_real.csv", "gray", "-"),
        ("Phase 7 (Winner)", sim_dir / "5months_phase7" / "trades_5months_phase7.csv", "blue", "-"),
        ("Exp 1 (ATR)", sim_dir / "5months_phase7_1_k2.2" / "trades_phase7_1.csv", "green", "--"),
        ("Exp 2 (Confirm)", sim_dir / "5months_phase7_1_fixed_confA" / "trades_phase7_1.csv", "orange", ":"),
        ("Exp 3 (Switch)", sim_dir / "5months_phase7_1_fixed_switch" / "trades_phase7_1.csv", "purple", "--"),
    ]
    
    plt.figure(figsize=(14, 8))
    
    for label, path, color, style in scenarios:
        df = load_equity(path, label)
        if df is not None:
            final_ret = df['return'].iloc[-1]
            plt.plot(df['time'], df['return']*100, label=f"{label}: {final_ret*100:.1f}%", color=color, linestyle=style, linewidth=2 if "Winner" in label else 1)
            
    plt.title("Final Strategy Comparison: The Journey to Phase 7", fontsize=16)
    plt.ylabel("Return (%)", fontsize=12)
    plt.xlabel("Date", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.axhline(0, color='black', linewidth=1)
    plt.legend(fontsize=12)
    
    # Annotations
    plt.annotate("Bear Market (Avoided by Phase 7)", xy=(pd.Timestamp("2025-09-15"), -10), 
                 xytext=(pd.Timestamp("2025-09-15"), -30), arrowprops=dict(facecolor='black', shrink=0.05))
                 
    plt.annotate("Bull Market (Captured by Phase 7)", xy=(pd.Timestamp("2025-11-15"), 20), 
                 xytext=(pd.Timestamp("2025-11-01"), 40), arrowprops=dict(facecolor='blue', shrink=0.05))

    out_path = sim_dir / "final_strategy_comparison.png"
    plt.savefig(out_path)
    print(f"Saved comparison chart to {out_path}")

if __name__ == "__main__":
    main()
