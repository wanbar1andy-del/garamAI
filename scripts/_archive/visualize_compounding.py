import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Set Korean Font
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def main():
    # Path to S4_narrow results (Standard k=1.0)
    results_dir = Path("g:/내 드라이브/garamdata/experiments/real_sim_champion_v3_final")
    equity_path = results_dir / "equity.csv"
    
    if not equity_path.exists():
        print(f"Error: Equity file not found at {equity_path}")
        return

    # Load Data
    df = pd.read_csv(equity_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Calculate Metrics
    initial_equity = df['equity'].iloc[0]
    final_equity = df['equity'].iloc[-1]
    total_return = (final_equity / initial_equity - 1) * 100
    cagr = ((final_equity / initial_equity) ** (252 / len(df)) - 1) * 100
    
    print(f"Initial: {initial_equity:,.0f}")
    print(f"Final:   {final_equity:,.0f}")
    print(f"Return:  {total_return:.2f}%")
    print(f"CAGR:    {cagr:.2f}%")

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # 1. Linear Scale (Absolute Growth)
    ax1.plot(df.index, df['equity'], color='#e74c3c', linewidth=2, label='Equity (Linear)')
    ax1.set_title(f'Equity Curve (Linear Scale) - Total Return: +{total_return:.2f}%', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity (KRW)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper left')
    
    # Format Y-axis as currency
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    # 2. Log Scale (Compounding Rate)
    ax2.plot(df.index, df['equity'], color='#2980b9', linewidth=2, label='Equity (Log Scale)')
    ax2.set_yscale('log')
    ax2.set_title(f'Compounding Effect (Log Scale) - Constant Slope = Steady Compounding', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Equity (Log Scale)', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7, which='both')
    ax2.legend(loc='upper left')

    # Format Date Axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    output_path = "c:/garam/garam/compounding_curve_s4_narrow.png"
    plt.savefig(output_path, dpi=300)
    print(f"Graph saved to: {output_path}")

if __name__ == "__main__":
    main()
