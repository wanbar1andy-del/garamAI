import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Paths
CSV_PATH = Path("c:/garam/garam/results/portfolio_stats.csv")
OUTPUT_PATH = Path("c:/garam/garam/results/oss_equity_curve_1.8b.png")

def plot_performance():
    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} not found.")
        return

    try:
        # Load Data (Format: timestamp,Total_Equity,Portfolio_Return) - WITH HEADER
        df = pd.read_csv(CSV_PATH) # Default header=0
        print(f"Columns set: {df.columns.tolist()}")
        
        # Identify columns
        time_col = df.columns[0]
        equity_col = df.columns[1]
        
        # Parse time
        df["time"] = pd.to_datetime(df[time_col])
        df.set_index("time", inplace=True)
        
        # Calculate Stats
        initial = df[equity_col].iloc[0]
        final = df[equity_col].iloc[-1]
        pnl = final - initial
        pnl_pct = (pnl / initial) * 100
        
        # Drawdown
        rolling_max = df[equity_col].cummax()
        drawdown = (df[equity_col] - rolling_max) / rolling_max * 100
        max_dd = drawdown.min()

        print(f"Initial: {initial:,.0f}")
        print(f"Final: {final:,.0f}")
        print(f"PnL: {pnl:,.0f} ({pnl_pct:.2f}%)")
        print(f"Max DD: {max_dd:.2f}%")

        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df[equity_col], label="Equity", color="#00ff00", linewidth=1.5)
        plt.title(f"OSS Brain Performance (8 Months)\nReturn: {pnl_pct:.2f}% | Final: {final:,.0f} KRW", color="white", fontsize=14)
        plt.xlabel("Date", color="white")
        plt.ylabel("Equity (KRW)", color="white")
        plt.grid(True, linestyle="--", alpha=0.3)
        plt.legend()
        
        # Dark Mode Style
        plt.gca().set_facecolor("#1e1e1e")
        plt.gcf().set_facecolor("#121212")
        plt.tick_params(colors="white")
        for spine in plt.gca().spines.values():
            spine.set_color("white")
            
        plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
        print(f"Chart saved to {OUTPUT_PATH}")

    except Exception as e:
        print(f"Plotting Error: {e}")

if __name__ == "__main__":
    plot_performance()
