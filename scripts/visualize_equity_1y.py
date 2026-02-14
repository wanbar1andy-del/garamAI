import pandas as pd
import matplotlib.pyplot as plt
import argparse
from pathlib import Path

def plot_equity(csv_path, output_path, title="Equity Curve"):
    df = pd.read_csv(csv_path)
    if "date" not in df.columns or "equity" not in df.columns:
        print("[FAIL] CSV must have 'date' and 'equity' columns")
        return

    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df = df.set_index("date")
    
    # Normalize to 100
    start_eq = df["equity"].iloc[0]
    df["normalized"] = (df["equity"] / start_eq) * 100
    
    # Drawdown
    roll_max = df["equity"].cummax()
    drawdown = (df["equity"] - roll_max) / roll_max * 100
    mdd = drawdown.min()
    
    final_return = df["normalized"].iloc[-1] - 100
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Equity
    ax1.plot(df.index, df["normalized"], label="Strategy", color="blue", linewidth=1.5)
    ax1.set_title(f"{title}\nReturn: +{final_return:.2f}% | MDD: {mdd:.2f}%")
    ax1.set_ylabel("Equity (Base 100)")
    ax1.grid(True, linestyle="--", alpha=0.7)
    ax1.legend()
    
    # Drawdown
    ax2.fill_between(df.index, drawdown, 0, color="red", alpha=0.3, label="Drawdown")
    ax2.set_ylabel("Drawdown %")
    ax2.set_xlabel("Date")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    print(f"[PLOT] Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="1-Year Walk Forward Equity")
    args = parser.parse_args()
    
    plot_equity(args.csv, args.out, args.title)
