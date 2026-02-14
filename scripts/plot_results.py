
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

def plot_equity():
    csv_path = "c:/garam/garam/results/GARAM_OSS_SHARE_RESULT.csv"
    output_path = "c:/garam/garam/results/equity_curve.png"
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    if 'equity' not in df.columns:
        print("Error: 'equity' column not found in CSV.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df['equity'], label='Equity Curve', color='#00d2ff', linewidth=2)
    
    # Styling
    plt.title('Garam OSS 2.1 Ultra - 5M Compounding Test', fontsize=16, color='white', fontweight='bold')
    plt.xlabel('Time (Minutes)', fontsize=12, color='white')
    plt.ylabel('Equity (KRW)', fontsize=12, color='white')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend()
    
    # Dark mode aesthetics
    plt.style.use('dark_background')
    plt.gca().set_facecolor('#1e1e1e')
    plt.gcf().set_facecolor('#121212')
    
    # Add final value annotation
    final_equity = df['equity'].iloc[-1]
    initial_equity = df['equity'].iloc[0]
    total_return = (final_equity / initial_equity - 1) * 100
    
    plt.annotate(f'Final: {final_equity:,.0f} ({total_return:+.2f}%)', 
                 xy=(len(df), final_equity), 
                 xytext=(0.8, 0.95), textcoords='axes fraction',
                 bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Graph saved to {output_path}")

if __name__ == "__main__":
    plot_equity()
