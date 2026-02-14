
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

CSV_PATH = "GARAM_Data/day1_allocation.csv"
OUT_PATH = "results/reports/day1_allocation_stacked.png"

def plot_allocation():
    if not os.path.exists(CSV_PATH):
        print("No allocation data.")
        return
        
    df = pd.read_csv(CSV_PATH, parse_dates=['ts'], index_col='ts')
    
    # 1. Convert to Portfolio Percentage
    # Strategy was 10M Cash. Total Value varies slightly, but lets use relative size.
    # Sum of row = Total Value Invested
    # We want Stacked Area of Value.
    
    # Sort columns by total allocation for better visual
    sums = df.sum()
    sorted_cols = sums.sort_values(ascending=False).index.tolist()
    df = df[sorted_cols]
    
    # Plot Stacked Area
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.stackplot(df.index, df.T, labels=df.columns, alpha=0.8)
    
    ax.set_title("Day-1 Portfolio Allocation (Concentration Rule Verification)")
    ax.set_ylabel("Position Value (KRW)")
    ax.set_xlabel("Time")
    
    # Annotate "Concentration"
    # Find max allocation of Top Symbol
    top_sym = df.columns[0]
    max_val = df[top_sym].max()
    
    ax.text(df.index[len(df)//2], max_val * 0.5, f"Hero {top_sym}\n(Concentration Target 60%)", 
            ha='center', va='center', color='white', fontweight='bold')

    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/10000)}W'))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH)
    print(f"Saved Allocation Chart: {OUT_PATH}")

if __name__ == "__main__":
    plot_allocation()
