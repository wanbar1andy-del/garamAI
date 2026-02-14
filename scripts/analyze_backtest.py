
import pandas as pd
import sys

def main():
    try:
        df = pd.read_csv("logs/phase30/backtest_3m_regime/A2/trades.csv")
    except FileNotFoundError:
        print("No trades file found.")
        return

    if df.empty:
        print("No trades found.")
        return

    # Filter out entry rows (keep only exit rows which have 'pnl')
    exits = df.dropna(subset=['pnl'])
    
    total_trades = len(exits)
    wins = exits[exits['pnl'] > 0]
    losses = exits[exits['pnl'] <= 0]
    
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    total_pnl = exits['pnl'].sum()
    gross_profit = wins['pnl'].sum()
    gross_loss = abs(losses['pnl'].sum())
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.0
    
    print(f"Total Trades: {total_trades}")
    print(f"Total PnL: {total_pnl:,.2f}")
    print(f"Win Rate: {win_rate*100:.2f}%")
    print(f"Profit Factor: {profit_factor:.2f}")
    
    print("\nExit Reasons:")
    print(exits['reason'].value_counts())
    
    print("\nTop Losers:")
    print(exits.sort_values('pnl').head(5)[['symbol', 'exit_ts', 'pnl', 'reason', 'return_pct']])

if __name__ == "__main__":
    main()
