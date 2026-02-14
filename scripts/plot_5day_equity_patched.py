
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from matplotlib.ticker import FuncFormatter

CSV_PATH = "GARAM_Data/5day_equity_patched.csv"
OUT_PATH = "results/reports/5day_equity_curve_patched.png"

def plot_5day():
    if not os.path.exists(CSV_PATH):
        print("No equity data.")
        return

    df = pd.read_csv(CSV_PATH)
    df["ts"] = pd.to_datetime(df["ts"])
    df.sort_values("ts", inplace=True)
    
    # Use Index for X-axis to remove Gaps
    df["idx"] = range(len(df))
    
    initial = 10_000_000
    df["return_pct"] = (df["Total_Equity"] - initial) / initial * 100.0

    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.plot(df["idx"], df["Total_Equity"], label="Asset (KRW)")
    ax1.set_ylabel("Total Asset (KRW)", fontweight="bold")
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
    
    # Optional: Set X-ticks to distinct dates only (to avoid clutter)
    # Finding indices where date changes
    df['date_str'] = df['ts'].dt.strftime('%m-%d')
    # simple approach: just let user confirm shape first
    
    ax2 = ax1.twinx()
    ax2.fill_between(df["idx"], df["return_pct"], 0, where=(df["return_pct"] >= 0), alpha=0.10)
    ax2.fill_between(df["idx"], df["return_pct"], 0, where=(df["return_pct"] < 0), alpha=0.10)
    ax2.set_ylabel("Return (%)", fontweight="bold")

    plt.title("5-Day Cumulative Profit (No Calendar Gaps)", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH)
    print(f"Saved: {OUT_PATH}")

if __name__ == "__main__":
    plot_5day()
