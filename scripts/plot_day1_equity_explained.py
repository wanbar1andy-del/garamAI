
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import os
import numpy as np

CSV_PATH = "GARAM_Data/day1_equity_diversified.csv"
OUT_PATH = "results/reports/day1_equity_curve_explained.png"

def plot_equity_explained():
    if not os.path.exists(CSV_PATH):
        print("No allocation data.")
        return
        
    df = pd.read_csv(CSV_PATH, parse_dates=['ts'], index_col='ts')
    
    if 'Total_Equity' not in df.columns:
        print("No Total_Equity column.")
        return
        
    # Initial Capital
    initial = 10000000
    
    # Calculate % Return
    df['return_pct'] = (df['Total_Equity'] - initial) / initial * 100.0
    
    # Plot Setup
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Left Axis: KRW
    color_krw = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Total Asset (KRW)', color=color_krw, fontweight='bold')
    ax1.plot(df.index, df['Total_Equity'], color=color_krw, linewidth=2, label='Asset Value (KRW)')
    ax1.tick_params(axis='y', labelcolor=color_krw)
    
    # Format KRW axis
    def krw_formatter(x, pos):
        return f'{int(x):,}'
    ax1.yaxis.set_major_formatter(FuncFormatter(krw_formatter))
    
    # Right Axis: % (With Fill)
    ax2 = ax1.twinx()  
    color_pct = 'tab:green'
    ax2.set_ylabel('Return (%)', color='black', fontweight='bold')
    
    # Fill Logic: Profit (Green) vs Loss (Red)
    ax2.fill_between(df.index, df['return_pct'], 0, where=(df['return_pct'] >= 0), color='green', alpha=0.1, label='Profit Zone')
    ax2.fill_between(df.index, df['return_pct'], 0, where=(df['return_pct'] < 0), color='red', alpha=0.1, label='Loss Zone')
    
    ax2.axhline(0, color='gray', linestyle='--', linewidth=1) # Break-even line
    
    # Customize Ticks
    ax2.tick_params(axis='y', labelcolor='black')
    
    # Title
    plt.title("Day-1 Asset Value & Return Analysis (Dual Axis)", fontsize=14)
    
    # Add Grid
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Annotate Min/Max
    min_val = df['Total_Equity'].min()
    max_val = df['Total_Equity'].max()
    min_ret = df['return_pct'].min()
    max_ret = df['return_pct'].max()
    
    # Show Min text
    min_idx = df['Total_Equity'].idxmin()
    ax1.annotate(f'Low: {int(min_val):,} (-{abs(min_ret):.2f}%)', 
                 xy=(min_idx, min_val), xytext=(min_idx, min_val - 50000),
                 arrowprops=dict(facecolor='red', shrink=0.05), color='red', fontweight='bold')

    # Show Max text
    max_idx = df['Total_Equity'].idxmax()
    ax1.annotate(f'High: {int(max_val):,} (+{max_ret:.2f}%)', 
                 xy=(max_idx, max_val), xytext=(max_idx, max_val + 50000),
                 arrowprops=dict(facecolor='green', shrink=0.05), color='green', fontweight='bold')

    plt.tight_layout()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH)
    print(f"Saved Explained Chart: {OUT_PATH}")

if __name__ == "__main__":
    plot_equity_explained()
