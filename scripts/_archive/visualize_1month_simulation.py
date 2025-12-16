import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import re

def parse_regimes(log_path):
    regimes = {}
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(log_path, 'r', encoding='cp949', errors='ignore') as f:
            lines = f.readlines()
            
    # Pattern: Detected Regime for YYYY-MM-DD: REGIME
    pattern = re.compile(r"Detected Regime for (\d{4}-\d{2}-\d{2}): (\w+)")
    
    for line in lines:
        match = pattern.search(line)
        if match:
            date_str = match.group(1)
            regime = match.group(2)
            regimes[date_str] = regime
    return regimes

def main():
    # Load Equity Data
    df = pd.read_csv("simulation_1month_equity.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # Load Regimes
    regimes = parse_regimes("c:/garam/garam/paper_trading.log")
    
    # Map Regimes to DataFrame
    df['regime'] = df['date'].astype(str).map(regimes)
    
    # Plot
    plt.figure(figsize=(12, 6))
    
    # Plot Equity Curve
    plt.plot(df['date'], df['equity'], label='Total Equity', color='blue', linewidth=2)
    
    # Highlight Crash Regimes
    # We want to shade areas where Regime is R7_CRASH or R6_DOWN
    # Since we have daily points, we can iterate and shade
    
    y_min, y_max = df['equity'].min(), df['equity'].max()
    margin = (y_max - y_min) * 0.1
    
    for i in range(len(df)):
        date = df.iloc[i]['date']
        regime = df.iloc[i]['regime']
        
        color = None
        label = None
        if regime == 'R7_CRASH':
            color = 'red'
            label = 'Crash (Cash Mode)'
        elif regime == 'R6_DOWN':
            color = 'orange'
            label = 'Down (Defensive)'
        elif regime == 'R5_DOWN_BOX':
            color = 'yellow'
            label = 'Down Box'
            
        if color:
            # Shade a bar around this date
            # Width is 1 day
            plt.axvspan(date - pd.Timedelta(days=0.5), date + pd.Timedelta(days=0.5), 
                        color=color, alpha=0.3)
            
            # Annotate if it's a switch (start of a block)
            if i > 0 and df.iloc[i-1]['regime'] != regime:
                plt.text(date, y_max + margin*0.2, regime, rotation=45, fontsize=8, color=color)

    plt.title("1-Month Simulation Equity Curve (Weighted 400 + Regime Aware)")
    plt.xlabel("Date")
    plt.ylabel("Equity (KRW)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    
    # Format Date Axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.gcf().autofmt_xdate()
    
    # Save
    save_path = "simulation_1month_equity.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {save_path}")

if __name__ == "__main__":
    main()
