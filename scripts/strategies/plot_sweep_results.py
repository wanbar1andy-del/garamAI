
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

LOG_DIR = Path("C:/garam/garam/logs/phase4_sweep")
OUT_FILE = LOG_DIR / "sweep_comparison.png"

def plot_results():
    files = {
        "Pyramid (Baseline)": LOG_DIR / "equity_PYRAMID_0.7.csv",
        "Pyramid (AESTHETIC)": LOG_DIR / "equity_PYRAMID_0.7_AESTHETIC.csv"
    }
    
    plt.figure(figsize=(12, 6))
    
    for label, fpath in files.items():
        if fpath.exists():
            df = pd.read_csv(fpath)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Normalize to Initial Capital
            df['return'] = (df['equity'] / df['equity'].iloc[0] - 1) * 100
            
            plt.plot(df.index, df['return'], label=f"{label} (Final: {df['return'].iloc[-1]:.1f}%)")
            
    plt.title("Garam Phase 4 Sweep: Allocation Strategy Comparison")
    plt.ylabel("Return (%)")
    plt.xlabel("Date")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_FILE)
    print(f"Saved chart to {OUT_FILE}")

if __name__ == "__main__":
    plot_results()
