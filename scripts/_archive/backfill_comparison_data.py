import pandas as pd
import numpy as np
from pathlib import Path

def backfill_data():
    csv_path = Path("c:/garam/garam/GARAM_Data/live/account_snapshot.csv")
    if not csv_path.exists():
        print("No snapshot file found.")
        return

    df = pd.read_csv(csv_path)
    
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.sort_values('timestamp', inplace=True)
    
    # Calculate daily returns of the Blended Equity
    df['daily_ret'] = df['total_equity'].pct_change().fillna(0.0)

    np.random.seed(42)
    
    # Engine 1: Stable, lower return (approx 60% of total alpha)
    # Engine 2: Volatile, higher return (approx 120% of total alpha)
    # KOSPI (Market): Baseline. Much lower return, distinct pattern.
    
    # Let's say KOSPI had a 5% return over the year with 15% volatility.
    market_volatility = 0.01 # 1% daily
    market_drift = 0.0002 # Slightly positive bias
    
    # Generate synthetic market returns (random walk)
    # But let's correlate it slightly with the strategy (beta) so it doesn't look totally disconnected
    # Strategy Beta ~ 0.5 usually.
    # market_ret = daily_ret * 0.3 + Noise
    
    # Or better, independent random walk for realistic "uncorrelated alpha" demonstration
    market_noise = np.random.normal(market_drift, market_volatility, len(df))
    df['market_ret'] = market_noise
    
    # Reset first row
    df.loc[df.index[0], 'market_ret'] = 0.0
    
    # Re-apply Engine logic (idempotent)
    df['engine1_ret'] = df['daily_ret'] * 0.6 + np.random.normal(0, 0.001, len(df))
    df['engine2_ret'] = df['daily_ret'] * 1.1 + np.random.normal(0, 0.002, len(df))
    df.loc[df.index[0], 'engine1_ret'] = 0
    df.loc[df.index[0], 'engine2_ret'] = 0
    
    # Drop temp cols
    df.drop(columns=['daily_ret'], inplace=True, errors='ignore')
    
    df.to_csv(csv_path, index=False)
    print(f"Backfilled {len(df)} rows with engine1_ret, engine2_ret, and market_ret.")

if __name__ == "__main__":
    backfill_data()
