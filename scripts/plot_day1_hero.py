
import pandas as pd
import matplotlib.pyplot as plt
import os

DATA_PATH = "GARAM_Data/day1_replay/319400.csv"
OUT_PATH = "results/reports/day1_hero_319400.png"

def plot_hero():
    if not os.path.exists(DATA_PATH):
        print(f"Data not found: {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH, parse_dates=['ts'], index_col='ts')
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Price
    ax1.plot(df.index, df['close'], label='Close', color='blue')
    ax1.set_title("Hero 319400 (2026-01-02) Intraday Action")
    ax1.set_ylabel("Price")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Volume
    ax2.bar(df.index, df['volume'], label='Volume', color='orange', width=0.0005) # Width is tricky with datetime
    ax2.set_ylabel("Volume")
    ax2.grid(True, alpha=0.3)
    
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH)
    print(f"Saved chart to {OUT_PATH}")

if __name__ == "__main__":
    plot_hero()
