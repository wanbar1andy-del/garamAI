
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.dates as mdates

# Config
LOG_DIR = Path("C:/garam/garam/logs/y1_daily")
EQ_FILE = LOG_DIR / "equity.csv"
OUT_FILE = LOG_DIR / "equity_chart.png"

def plot_performance():
    if not EQ_FILE.exists():
        print(f"Error: {EQ_FILE} not found.")
        return

    # Load Data
    df = pd.read_csv(EQ_FILE)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Calculate Stats
    df['peak'] = df['equity'].cummax()
    df['dd'] = (df['equity'] - df['peak']) / df['peak']
    
    final_ret = (df['equity'].iloc[-1] / 100_000_000 - 1) * 100
    max_dd = df['dd'].min() * 100
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Equity Curve
    ax1.plot(df.index, df['equity'], label='Portfolio Equity', color='blue', linewidth=2)
    ax1.set_title(f"Project Y-7 Performance (Return: +{final_ret:.2f}%)", fontsize=14)
    ax1.set_ylabel("Equity (KRW)")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Format Y-axis to Millions
    def millions(x, pos):
        return '%1.0fM' % (x * 1e-6)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(millions))
    
    # Drawdown Curve
    ax2.fill_between(df.index, df['dd'] * 100, 0, color='red', alpha=0.3, label='Drawdown')
    ax2.plot(df.index, df['dd'] * 100, color='red', linewidth=1)
    ax2.set_title(f"Drawdown (Max: {max_dd:.2f}%)", fontsize=12)
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)
    
    # Format X-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(OUT_FILE)
    print(f"Chart saved to {OUT_FILE}")

if __name__ == "__main__":
    plot_performance()
