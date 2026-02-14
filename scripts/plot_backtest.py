
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

def main():
    log_dir = Path("logs/phase30/backtest_3m_regime/A2")
    equity_file = log_dir / "equity_curve.csv"
    
    if not equity_file.exists():
        print(f"Error: {equity_file} not found.")
        return

    df = pd.read_csv(equity_file)
    df['ts'] = pd.to_datetime(df['ts'])
    df = df.set_index('ts')
    
    # Calculate stats
    initial_equity = df['equity'].iloc[0]
    final_equity = df['equity'].iloc[-1]
    ret = (final_equity / initial_equity) - 1.0
    
    # MDD
    rolling_max = df['equity'].cummax()
    drawdown = (df['equity'] - rolling_max) / rolling_max
    mdd = drawdown.min()
    
    # Plot
    plt.figure(figsize=(12, 6))
    
    # Top: Equity
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(df.index, df['equity'], label='Equity', color='blue')
    ax1.set_title(f"Alpha A2 (Regime Filter) - 3 Month Backtest\nReturn: {ret*100:.2f}% | MDD: {mdd*100:.2f}%")
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax1.legend()
    
    # Format Y axis (Thousands)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    # Bottom: Drawdown
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    ax2.fill_between(df.index, drawdown, 0, color='red', alpha=0.3, label='Drawdown')
    ax2.set_title("Drawdown")
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax2.legend()
    
    plt.tight_layout()
    
    out_file = log_dir / "backtest_3m_A2_equity.png"
    plt.savefig(out_file)
    print(f"Saved plot to {out_file}")
    print(f"MDD: {mdd:.4f}")

if __name__ == "__main__":
    main()
