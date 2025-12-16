import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import sys
from pathlib import Path

# Set Korean Font (Malgun Gothic for Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def main():
    # 1. Define Paths
    # Use raw string for Windows path or forward slashes
    results_dir = Path("g:/내 드라이브/garamdata/experiments/real_sim_champion_v3_final")
    
    print(f"Loading results from: {results_dir}")
    
    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}")
        # Try finding it relative to project root if G: is mapped differently
        # But let's just list what we can see
        return

    equity_path = results_dir / "equity.csv"
    trades_path = results_dir / "trades.csv"
    
    if not equity_path.exists():
        print(f"Error: Equity file not found at {equity_path}")
        print("Contents of dir:")
        for p in results_dir.glob("*"):
            print(f"  {p.name}")
        return

    # 2. Load Data
    try:
        df_equity = pd.read_csv(equity_path)
    except Exception as e:
        print(f"Error reading equity csv: {e}")
        return

    if 'date' in df_equity.columns:
        df_equity['date'] = pd.to_datetime(df_equity['date'])
        df_equity.set_index('date', inplace=True)
    
    # Load Trades
    df_trades = pd.DataFrame()
    if trades_path.exists():
        try:
            df_trades = pd.read_csv(trades_path)
            if 'entry_time' in df_trades.columns:
                df_trades['entry_time'] = pd.to_datetime(df_trades['entry_time'])
        except Exception as e:
            print(f"Error reading trades csv: {e}")

    # 3. Prepare Data for Plotting
    # Equity Curve (Normalized)
    initial_equity = df_equity['equity'].iloc[0]
    df_equity['Strategy'] = (df_equity['equity'] / initial_equity) * 100
    
    # Benchmark (if available)
    if 'benchmark' in df_equity.columns:
        initial_bench = df_equity['benchmark'].iloc[0]
        df_equity['Benchmark'] = (df_equity['benchmark'] / initial_bench) * 100

    # Drawdown
    # Calculate Drawdown manually if not present
    if 'drawdown' not in df_equity.columns:
        running_max = df_equity['equity'].cummax()
        df_equity['Drawdown'] = (df_equity['equity'] - running_max) / running_max * 100
    else:
        df_equity['Drawdown'] = df_equity['drawdown'] * 100 # Convert to %

    # Trade Frequency (Daily)
    if not df_trades.empty:
        daily_trades = df_trades.groupby('entry_time').size()
        daily_trades = daily_trades.reindex(df_equity.index).fillna(0)
    else:
        daily_trades = pd.Series(0, index=df_equity.index)

    # 4. Create Plot
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1], hspace=0.3)

    # Ax1: Equity Curve
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(df_equity.index, df_equity['Strategy'], label='Strategy (A5+A6+A7)', color='#ff4757', linewidth=2)
    if 'Benchmark' in df_equity.columns:
        ax1.plot(df_equity.index, df_equity['Benchmark'], label='KOSPI (Benchmark)', color='#2f3542', linestyle='--', alpha=0.7)
    
    ax1.set_title('Strategy Performance vs Benchmark (1 Year)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Normalized Equity (Start=100)', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Ax2: Drawdown
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.fill_between(df_equity.index, df_equity['Drawdown'], 0, color='#e17055', alpha=0.5, label='Drawdown')
    ax2.plot(df_equity.index, df_equity['Drawdown'], color='#d63031', linewidth=1)
    ax2.set_ylabel('Drawdown (%)', fontsize=12)
    ax2.set_title('Drawdown Risk', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # Ax3: Trade Frequency
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.bar(daily_trades.index, daily_trades.values, color='#0984e3', alpha=0.7, label='Daily Trades')
    ax3.set_ylabel('Trade Count', fontsize=12)
    ax3.set_title('Trading Activity (Frequency)', fontsize=12)
    ax3.grid(True, axis='y', linestyle='--', alpha=0.5)

    # Formatting Dates
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax3.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

    # Save
    output_path = "c:/garam/garam/simulation_result_graph.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Graph saved to: {output_path}")

if __name__ == "__main__":
    main()
