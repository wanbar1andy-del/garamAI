
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("C:/garam/garam/GARAM_Data/60day_replay_kst")
LOG_DIR = Path("C:/garam/garam/logs/y1_daily")

# 1. Load Equity
eq_df = pd.read_csv(LOG_DIR / "equity.csv")
eq_df['date'] = pd.to_datetime(eq_df['date'])
eq_df.set_index('date', inplace=True)

# 2. Calculate Market Breadth (Stocks > MA20)
print("Loading Universe for Breadth Analysis...")
files = list(DATA_DIR.glob("*.csv"))
breadth_data = []

for f in files:
    if 'K' in f.name: continue
    try:
        df = pd.read_csv(f)
        # Standardize Columns
        cols = {c.lower(): c for c in df.columns}
        rename_map = {}
        if 'ts' in cols: rename_map[cols['ts']] = 'date'
        elif 'date' in cols: rename_map[cols['date']] = 'date'
        for k in ['close']:
            if k in cols: rename_map[cols[k]] = k
        df.rename(columns=rename_map, inplace=True)
        
        if 'date' not in df.columns or 'close' not in df.columns: continue
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Resample to Daily
        daily = df.resample('1D').agg({'close': 'last'}).dropna()
        if daily.empty: continue
        
        # Calc MA20
        daily['ma20'] = daily['close'].rolling(20).mean()
        daily['above_ma20'] = (daily['close'] > daily['ma20']).astype(int)
        
        breadth_data.append(daily['above_ma20'])
    except:
        pass

# Aggregate
if not breadth_data:
    print("No data found.")
    exit()

print(f"Loaded {len(breadth_data)} tickers.")
breadth_df = pd.concat(breadth_data, axis=1)
breadth_df.fillna(0, inplace=True)

# Calculate Daily Ratio
market_stats = pd.DataFrame()
market_stats['count'] = breadth_df.sum(axis=1)
market_stats['total'] = breadth_df.count(axis=1) 
market_stats['ratio'] = market_stats['count'] / len(breadth_data)

# Calculate Momentum
market_stats['ratio_delta'] = market_stats['ratio'].diff()
market_stats['ratio_chg'] = market_stats['ratio'].pct_change()

# Merge with Equity
merged = market_stats.join(eq_df, how='inner')
merged['equity_norm'] = merged['equity'] / merged['equity'].iloc[0]

print("\n--- Market Breadth vs Equity ---")
print(merged[['ratio', 'ratio_delta', 'equity', 'equity_norm']].tail(20))

# Calculate Drawdown for context
merged['peak'] = merged['equity'].cummax()
merged['dd'] = (merged['equity'] - merged['peak']) / merged['peak']

# Check Crash Period
print("\n--- Crash Period Analysis (Dec 12 - Dec 20) ---")
print(merged.loc['2025-12-12':'2025-12-20'][['ratio', 'ratio_delta', 'equity', 'dd']])


# Correlation
corr = merged['ratio'].corr(merged['equity'])
print(f"\nCorrelation (Ratio vs Equity): {corr:.4f}")

# Check Drawdown Period (Late Dec)
print("\nLate Dec Stats:")
print(merged.loc['2025-12-15':'2025-12-30'])
