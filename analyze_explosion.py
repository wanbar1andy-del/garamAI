import pandas as pd
import sys

def main():
    try:
        df = pd.read_csv("results/phase29/backtest/A6/trades.csv")
    except:
        print("No trades file.")
        return

    # Check for huge pnl
    # Convert to numeric
    df["pnl"] = pd.to_numeric(df["pnl"], errors='coerce').fillna(0.0)
    df["entry_px"] = pd.to_numeric(df["entry_px"], errors='coerce').fillna(0.0)
    df["qty"] = pd.to_numeric(df["qty"], errors='coerce').fillna(0.0)
    
    # Sort by time?
    # It might be in order.
    
    threshold = 10_000_000 # 10M KRW profit/loss in one trade
    
    # Print first 100 trades
    print("First 60 trades:")
    print(df.head(60))
    
    # Check for any positive PnL > 1,000,000
    pos_huge = df[df["pnl"] > 1_000_000]
    if not pos_huge.empty:
        print("\nHuge Positive Trades:")
        print(pos_huge.head())
        
    # Check if entry_px is 0 or tiny?
    tiny_px = df[(df["entry_px"] > 0) & (df["entry_px"] < 100)]
    if not tiny_px.empty:
        print("\nTiny Entry Prices found:")
        print(tiny_px.head())

if __name__ == "__main__":
    main()
