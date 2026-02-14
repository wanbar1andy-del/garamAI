
import pandas as pd
import numpy as np
from pathlib import Path

# Load Logs
log_dir = Path("C:/garam/garam/logs/y1_daily")
trades = pd.read_csv(log_dir / "trade_log.csv")
trades['date'] = pd.to_datetime(trades['date'])

# Load Universe Data for 229640
ticker = "229640" 
data_file = list(Path("C:/garam/garam/GARAM_Data/60day_replay_kst").glob(f"*{ticker}*"))[0]
df = pd.read_csv(data_file)
# ... standard loading/resampling code trace ...
# To be quick, just looking at the log might be enough if we logged market ratio.
# But we only logged market ratio on Exits.

# Let's reconstruct or reuse the DailyTrendEngine to inspect state if possible,
# or just analyze the trade log if it has enough info.
# The trade log has 'market_ratio' column added in Y-6.

print("--- Market Ratio on Exits around Dec 16 ---")
dec_trades = trades[(trades['date'] >= '2025-12-10') & (trades['date'] <= '2025-12-20')]
print(dec_trades[['date', 'ticker', 'side', 'reason', 'market_ratio', 'pnl']].dropna(subset=['market_ratio']))

# Detailed look at 229640
print("\n--- 229640 Trade History ---")
print(trades[trades['ticker'].astype(str).str.contains(ticker)])

# We need to know the ATR and Entry Price to check if 2.0 ATR should have hit.
# The log doesn't have ATR.
# But we can infer max adverse excursion.
