
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load Logs
log_dir = Path("C:/garam/garam/logs/y1_daily")
trades = pd.read_csv(log_dir / "trade_log.csv")
print("--- Exit Reason Summary (Y-7 Intraday) ---")

exits = trades[trades['side'] == 'SELL']

# Group by Reason
# We expect "Intraday" tags
summary = exits.groupby('reason')['pnl'].agg(['count', 'mean', 'sum'])
summary['mean_pnl_pct'] = (summary['sum'] / 100_000_000) * 100
print(summary)

# Check for Gap Downs (Price < Expected Stop)
# Use 'Trailing Stop' reasons
trailing = exits[exits['reason'].str.contains('Trailing Stop')]
print(f"\nTotal Trailing Stops: {len(trailing)}")
print(trailing[['date', 'ticker', 'price', 'pnl', 'reason']].head(10))

# Analyze Performance Drop
print("\n--- Performance Drop Analysis ---")
print(f"Total PnL Sum: {trades['pnl'].sum():,.0f} KRW")
print("Compare with Y-6 (~28M KRW)")
