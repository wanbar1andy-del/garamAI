
import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_x6c():
    exclude_columns = ['regime', 'signals']
    
    # Load Main Data (X-6c)
    df_c = pd.read_csv("GARAM_Data/x6c_daily.csv")
    df_c['date'] = pd.to_datetime(df_c['date'])
    
    # Load Baseline Data (X-6) if implies Ban Only
    df_b = None
    if os.path.exists("GARAM_Data/x6_daily.csv"):
        df_b = pd.read_csv("GARAM_Data/x6_daily.csv")
        df_b['date'] = pd.to_datetime(df_b['date'])

    plt.figure(figsize=(12, 6))
    
    # Plot X-6c
    plt.plot(df_c['date'], df_c['equity'], label='X-6c (Active Recovery)', color='blue', linewidth=2)
    
    # Plot X-6b (Baseline)
    if df_b is not None:
        # Align dates
        plt.plot(df_b['date'], df_b['equity'], label='X-6b (Passive Ban)', color='gray', linestyle='--', alpha=0.7)

    # Highlight Regimes in X-6c
    # We want to shade background based on regime
    # regime states: NORMAL, BAN, RECOVERY
    # We iterate and find segments
    
    y_min, y_max = plt.ylim()
    
    # Create simple segments
    for i in range(len(df_c)-1):
        d1 = df_c.iloc[i]['date']
        d2 = df_c.iloc[i+1]['date']
        regime = df_c.iloc[i]['regime']
        
        color = 'white'
        if regime == 'BAN': color = '#ffcccc' # Light Red
        elif regime == 'RECOVERY': color = '#ccffcc' # Light Green
        
        if color != 'white':
            plt.axvspan(d1, d2, color=color, alpha=0.3, linewidth=0)

    plt.title("Phase X-6c: Regime Recovery Verification (Ban vs Unban)")
    plt.ylabel("Equity (KRW)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path = "GARAM_Data/phase_x6c_comparison.png"
    plt.savefig(output_path)
    print(f"Graph saved to {output_path}")

if __name__ == "__main__":
    plot_x6c()
