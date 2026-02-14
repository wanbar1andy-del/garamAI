
import pandas as pd
from pathlib import Path

# Load Logs
log_dir = Path("C:/garam/garam/logs/y1_daily")
trades = pd.read_csv(log_dir / "trade_log.csv")

print("--- Y-8 Climax Profit Analysis ---")
climax_exits = trades[trades['reason'].str.contains('Climax', na=False)]

print(f"Total Climax Exits: {len(climax_exits)}")
if not climax_exits.empty:
    print(climax_exits[['date', 'ticker', 'price', 'qty', 'pnl']])
    print(f"Total Profit from Climax: {climax_exits['pnl'].sum():,.0f} KRW")

# Check Total PnL compared to Y-7
print(f"\nTotal Portfolio PnL: {trades['pnl'].sum():,.0f} KRW")
print(f"(Y-7 was ~13M KRW)")

# Investigation: Did we miss a big run?
# Check SK Hynix trades
print("\n--- SK Hynix Trades ---")
print(trades[trades['ticker'].astype(str).str.contains('660')])
