
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from matplotlib.ticker import FuncFormatter

CSV_PATH = "GARAM_Data/5day_equity.csv"
OUT_PATH = "results/reports/5day_equity_curve.png"

def plot_5day():
    if not os.path.exists(CSV_PATH):
        print("No equity data.")
        return
        
    df = pd.read_csv(CSV_PATH, parse_dates=['ts'], index_col='ts')
    
    # Capital
    initial = 10000000
    df['return_pct'] = (df['Total_Equity'] - initial) / initial * 100.0
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Dual Axis
    color_krw = 'tab:blue'
    ax1.plot(df.index, df['Total_Equity'], color=color_krw, label='Asset (KRW)')
    ax1.set_ylabel('Total Asset (KRW)', color=color_krw, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color_krw)
    
    def krw_formatter(x, pos): return f'{int(x):,}'
    ax1.yaxis.set_major_formatter(FuncFormatter(krw_formatter))
    
    ax2 = ax1.twinx()
    # Profit/Loss Fill
    ax2.fill_between(df.index, df['return_pct'], 0, where=(df['return_pct'] >= 0), color='green', alpha=0.1)
    ax2.fill_between(df.index, df['return_pct'], 0, where=(df['return_pct'] < 0), color='red', alpha=0.1)
    ax2.set_ylabel('Return (%)', color='black', fontweight='bold')
    
    plt.title("5-Day Cumulative Profit (Simulated)", fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Date formatting for 5 days
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH)
    print(f"Saved: {OUT_PATH}")

if __name__ == "__main__":
    plot_5day()
