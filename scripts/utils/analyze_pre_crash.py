
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load Data
DATA_DIR = Path("C:/garam/garam/GARAM_Data/60day_replay_kst")
LOG_DIR = Path("C:/garam/garam/logs/y1_daily")

# Load Equity to pinpoint peak
eq_df = pd.read_csv(LOG_DIR / "equity.csv")
eq_df['date'] = pd.to_datetime(eq_df['date'])
eq_df.set_index('date', inplace=True)
peak_date = eq_df['equity'].idxmax()
print(f"Equity Peak: {peak_date}")

# Calculate Market Indicators around Peak (Nov 20 - Dec 15)
start_date = "2025-11-20"
end_date = "2025-12-20"

print(f"Analyzing {start_date} ~ {end_date}...")

files = list(DATA_DIR.glob("*.csv"))
daily_stats = []

for f in files:
    if 'K' in f.name: continue
    try:
        df = pd.read_csv(f)
        # Standardize
        cols = {c.lower(): c for c in df.columns}
        rename_map = {}
        if 'ts' in cols: rename_map[cols['ts']] = 'date'
        elif 'date' in cols: rename_map[cols['date']] = 'date'
        for k in ['open','high','low','close','volume']:
            if k in cols: rename_map[cols[k]] = k
        df.rename(columns=rename_map, inplace=True)
        if 'date' not in df.columns or 'close' not in df.columns: continue
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        daily = df.resample('1D').agg({'close': 'last', 'volume': 'sum'}).dropna()
        if daily.empty: continue
        
        # Breadth: Close > MA20
        daily['ma20'] = daily['close'].rolling(20).mean()
        daily['above_ma20'] = (daily['close'] > daily['ma20']).astype(int)
        
        daily_stats.append(daily)
    except: pass

# Aggregate
# We need daily aggregate of 'above_ma20' count and 'total' count
# Also maybe Avg Turnover?

# Re-structure: Create a DF with columns as tickers for 'above_ma20'
if not daily_stats: exit()

# It's hard to merge 400 dfs quickly.
# Let's iterate dates.
all_dates = pd.date_range(start_date, end_date)
market_metrics = []

for d in all_dates:
    d_str = d.strftime('%Y-%m-%d')
    # Filter valid tickers for this day
    # This loop is inefficient but acceptable for analysis script
    
    count_above = 0
    total_active = 0
    total_to = 0
    
    for df in daily_stats:
        if d in df.index:
            row = df.loc[d]
            total_active += 1
            if row['above_ma20'] == 1:
                count_above += 1
            total_to += row['close'] * row['volume']
            
    if total_active > 0:
        market_metrics.append({
            'date': d,
            'breadth_ratio': count_above / total_active,
            'total_turnover': total_to,
            'active_count': total_active
        })

metrics_df = pd.DataFrame(market_metrics)
metrics_df.set_index('date', inplace=True)

# Merge with Equity
merged = metrics_df.join(eq_df[['equity']])

print("\n--- Pre-Crash Indicators ---")
print(merged)

# Check Divergence
# Did Breadth Ratio drop while Equity was rising?
merged['equity_chg'] = merged['equity'].pct_change()
merged['breadth_chg'] = merged['breadth_ratio'].pct_change()

print("\n--- Daily Changes ---")
print(merged[['equity', 'breadth_ratio', 'total_turnover']].tail(15))
