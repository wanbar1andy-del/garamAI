
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load Equity Curve
eq_file = Path("C:/garam/garam/logs/y1_daily/equity.csv")
df = pd.read_csv(eq_file)
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# Calculate Drawdown
df['peak'] = df['equity'].cummax()
df['dd'] = (df['equity'] - df['peak']) / df['peak']
max_dd = df['dd'].min()

print(f"Max Drawdown: {max_dd*100:.2f}%")

# Load Trade Log for Hindrance Analysis
log_file = Path("C:/garam/garam/logs/y1_daily/trade_log.csv")
trades = pd.read_csv(log_file)
exits = trades[trades['side'] == 'SELL']

# Check Adaptive Stops (2.0 vs 3.0)
print("\n--- Exit Reason Summary ---")
summary = exits.groupby('reason')['pnl'].agg(['count', 'mean', 'sum'])
print(summary)

# Check specific "Bear Market" exits
print("\n--- Adaptive Stop Analysis (Bear Market) ---")
# Filter for Trailing Stop (2.0ATR)
tight_stops = exits[exits['reason'].str.contains('2.0ATR', na=False)]
print(f"Tight Stops Triggered: {len(tight_stops)}")
if not tight_stops.empty:
    print(tight_stops[['date', 'ticker', 'price', 'pnl']].head())

# Check SK Hynix
print("\nSK Hynix Status:")
print(trades[trades['ticker'].astype(str).str.contains('660')])
