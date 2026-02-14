
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

CSV_PATH = "GARAM_Data/day1_allocation.csv"
OUT_PATH = "results/reports/day1_equity_curve.png"

def plot_equity():
    if not os.path.exists(CSV_PATH):
        print("No allocation data.")
        return
        
    df = pd.read_csv(CSV_PATH, parse_dates=['ts'], index_col='ts')
    
    if 'Total_Equity' not in df.columns:
        print("No Total_Equity column.")
        return
        
    # Plot Equity
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Initial Capital
    initial = 10000000
    
    # Calculate % Return
    df['return_pct'] = (df['Total_Equity'] - initial) / initial * 100.0
    
    ax.plot(df.index, df['return_pct'], label='Portfolio Return', color='green', linewidth=2)
    ax.fill_between(df.index, df['return_pct'], 0, color='green', alpha=0.1)
    
    ax.set_title("Day-1 Realized Cumulative Profit (Concentration Strategy)")
    ax.set_ylabel("Return (%)")
    ax.set_xlabel("Time")
    
    # Annotate Final Return
    final_ret = df['return_pct'].iloc[-1]
    ax.text(df.index[-1], final_ret, f"+{final_ret:.2f}%", ha='left', va='center', fontweight='bold', color='green')

    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH)
    print(f"Saved Equity Chart: {OUT_PATH}")

if __name__ == "__main__":
    plot_equity()
