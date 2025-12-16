import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Set Korean Font
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def main():
    results_dir = Path("g:/내 드라이브/garamdata/experiments/real_sim_champion_v3_final")
    
    # Load S9 (Profit Rest 1d - Best)
    path_s9 = results_dir / "equity_s9.csv"
    # Note: I didn't save S9 explicitly as equity_s9.csv, but I should have.
    # If not, I might need to rely on the fact that S9 was the previous run.
    # Actually, I didn't rename equity.csv to equity_s9.csv in the previous step.
    # I only have equity.csv (which is now S11) and equity_s4.csv.
    # This is a mistake in my process. I should have saved S9 result.
    # However, I know S9 result was +71.82%.
    # I can try to load S4 and S11.
    
    path_s4 = results_dir / "equity_s4.csv"
    if not path_s4.exists():
        print(f"Error: S4 results not found at {path_s4}")
        return
    df_s4 = pd.read_csv(path_s4)
    df_s4['date'] = pd.to_datetime(df_s4['date'])
    df_s4.set_index('date', inplace=True)
    
    # Load S11 (BB Exit)
    path_s11 = results_dir / "equity.csv"
    if not path_s11.exists():
        print(f"Error: S11 results not found at {path_s11}")
        return
    df_s11 = pd.read_csv(path_s11)
    df_s11['date'] = pd.to_datetime(df_s11['date'])
    df_s11.set_index('date', inplace=True)
    
    # Calculate Metrics
    ret_s4 = (df_s4['equity'].iloc[-1] / df_s4['equity'].iloc[0] - 1) * 100
    ret_s11 = (df_s11['equity'].iloc[-1] / df_s11['equity'].iloc[0] - 1) * 100
    
    mdd_s4 = ((df_s4['equity'] - df_s4['equity'].cummax()) / df_s4['equity'].cummax()).min() * 100
    mdd_s11 = ((df_s11['equity'] - df_s11['equity'].cummax()) / df_s11['equity'].cummax()).min() * 100
    
    print(f"S4 (Standard): Return {ret_s4:.2f}%, MDD {mdd_s4:.2f}%")
    print(f"S11 (BB Exit): Return {ret_s11:.2f}%, MDD {mdd_s11:.2f}%")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df_s4.index, df_s4['equity'], color='#95a5a6', linewidth=2, label=f'S4 (Standard): +{ret_s4:.2f}% (MDD {mdd_s4:.2f}%)')
    ax.plot(df_s11.index, df_s11['equity'], color='#9b59b6', linewidth=2, label=f'S11 (BB Exit): +{ret_s11:.2f}% (MDD {mdd_s11:.2f}%)')
    
    ax.set_title('Impact of BB Profit Exit (Price > Mid + 0.6*Width)', fontsize=14, fontweight='bold')
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
    
    output_path = "c:/garam/garam/comparison_s4_vs_s11.png"
    plt.savefig(output_path, dpi=300)
    print(f"Graph saved to: {output_path}")

if __name__ == "__main__":
    main()
