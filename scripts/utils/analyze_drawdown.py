
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

# Identify worst periods
worst_days = df.sort_values('dd').head(5)
print("\nWorst Drawdown Days:")
print(worst_days)

# Load Universe to check Market Breadth (Proxy Index)
# We can't easily load all files again here quickly, but we can check the log file for signal counts if we parsed it.
# Instead, let's just look at the equity curve for now.
