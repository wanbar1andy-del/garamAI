import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Set Korean Font
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def main():
    results_dir = Path("g:/내 드라이브/garamdata/experiments/real_sim_champion_v3_final")
    
    # Load S4 (Standard)
    path_s4 = results_dir / "equity_s4.csv"
    if not path_s4.exists():
        print(f"Error: S4 results not found at {path_s4}")
        return
    df_s4 = pd.read_csv(path_s4)
    df_s4['date'] = pd.to_datetime(df_s4['date'])
    df_s4.set_index('date', inplace=True)
    
    # Load S6 (Morning Stop)
    path_s6 = results_dir / "equity.csv"
    if not path_s6.exists():
        print(f"Error: S6 results not found at {path_s6}")
        return
    df_s6 = pd.read_csv(path_s6)
    df_s6['date'] = pd.to_datetime(df_s6['date'])
    df_s6.set_index('date', inplace=True)
    
    # Calculate Metrics
    ret_s4 = (df_s4['equity'].iloc[-1] / df_s4['equity'].iloc[0] - 1) * 100
    ret_s6 = (df_s6['equity'].iloc[-1] / df_s6['equity'].iloc[0] - 1) * 100
    
    mdd_s4 = ((df_s4['equity'] - df_s4['equity'].cummax()) / df_s4['equity'].cummax()).min() * 100
    mdd_s6 = ((df_s6['equity'] - df_s6['equity'].cummax()) / df_s6['equity'].cummax()).min() * 100
    
    print(f"S4 (Standard): Return {ret_s4:.2f}%, MDD {mdd_s4:.2f}%")
    print(f"S6 (Morning Stop): Return {ret_s6:.2f}%, MDD {mdd_s6:.2f}%")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df_s4.index, df_s4['equity'], color='#95a5a6', linewidth=2, label=f'S4 (Standard): +{ret_s4:.2f}% (MDD {mdd_s4:.2f}%)')
    ax.plot(df_s6.index, df_s6['equity'], color='#e74c3c', linewidth=2, label=f'S6 (Morning Stop): +{ret_s6:.2f}% (MDD {mdd_s6:.2f}%)')
    
    ax.set_title('Impact of Morning Stop-Loss (Exit at Open if Gap Down)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Equity (KRW)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')
    
    # Format Y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    # Format Date Axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    output_path = "c:/garam/garam/comparison_s4_vs_s6.png"
    plt.savefig(output_path, dpi=300)
    print(f"Graph saved to: {output_path}")

if __name__ == "__main__":
    main()
