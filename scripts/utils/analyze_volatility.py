
import pandas as pd
import numpy as np
from pathlib import Path

# Load Logs
log_dir = Path("C:/garam/garam/logs/y1_daily")
trades = pd.read_csv(log_dir / "trade_log.csv")

# Identify positions held on Dec 12
start_date = "2025-12-10"
end_date = "2025-12-16"

# We need to know what we held.
# Let's reconstruct holdings from trade log? Hard.
# Better to use the 'daily_trend_engine' logic or just check the stocks that caused losses.
# From previous analysis, losers were: 229640, 294870, 030530?
# Let's check the top holdings on Dec 12.

# Load raw universe data for key tickers
targets = ['229640', '030530', '010130', '294870'] # Losers identified in Step 22610
DATA_DIR = Path("C:/garam/garam/GARAM_Data/60day_replay_kst")

print(f"--- Analyzing Volatility & Turnover ({start_date} ~ {end_date}) ---")

for tkr in targets:
    f_list = list(DATA_DIR.glob(f"{tkr}*.csv"))
    if not f_list: continue
    
    df = pd.read_csv(f_list[0])
    # Standardize
    cols = {c.lower(): c for c in df.columns}
    rename_map = {}
    if 'ts' in cols: rename_map[cols['ts']] = 'date'
    elif 'date' in cols: rename_map[cols['date']] = 'date'
    for k in ['open','high','low','close','volume']:
        if k in cols: rename_map[cols[k]] = k
    df.rename(columns=rename_map, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Resample Daily
    daily = df.resample('1D').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    
    # Calc Indicators
    daily['turnover'] = daily['close'] * daily['volume']
    daily['tr'] = np.maximum(daily['high'] - daily['low'], 
                             np.maximum(np.abs(daily['high'] - daily['close'].shift()), 
                                        np.abs(daily['low'] - daily['close'].shift())))
    daily['atr'] = daily['tr'].rolling(14).mean()
    daily['atr_pct'] = daily['atr'] / daily['close']
    daily['to_ma5'] = daily['turnover'].rolling(5).mean()
    daily['to_ratio'] = daily['turnover'] / daily['to_ma5']
    
    subset = daily.loc[start_date:end_date]
    if not subset.empty:
        print(f"\nTicker: {tkr}")
        print(subset[['close', 'atr_pct', 'turnover', 'to_ratio']])
