import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Setup Path
sys.path.append(os.path.abspath("C:/garam/garam"))

try:
    from config import PATHS
except ImportError:
    from garam.config import PATHS

from garam.engine.components.hmm_detector import HMMRegimeDetector

def load_data():
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    df_mkt = pd.read_csv(kospi_path)
    col_map = {c: c.lower() for c in df_mkt.columns}
    df_mkt.rename(columns=col_map, inplace=True)
    date_col = 'timestamp' if 'timestamp' in df_mkt.columns else 'date'
    df_mkt[date_col] = pd.to_datetime(df_mkt[date_col])
    df_mkt.set_index(date_col, inplace=True)
    df_mkt.sort_index(inplace=True)
    df_mkt['ret_mkt'] = df_mkt['close'].pct_change().fillna(0.0)
    
    # 10 Year Window
    start_date = pd.Timestamp("2015-01-01")
    df_10y = df_mkt[df_mkt.index >= start_date].copy()
    
    return df_10y, df_mkt

def check_turbo_risk():
    print("=== Checking Turbo Risk (Liquidation Safety) ===")
    try:
        df, df_full = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # Train HMM
    train_data = df_full[df_full.index < df.index[0]]['close']
    hmm = HMMRegimeDetector()
    hmm.train(train_data)
    
    TURBO_MULT = 2.5
    
    turbo_days = []
    
    for date, row in df.iterrows():
        recent_data = df_full.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        
        if regime == 'BULL':
            # Turbo ON
            day_ret = row['ret_mkt']
            leveraged_ret = day_ret * TURBO_MULT
            turbo_days.append({
                'date': date,
                'market_ret': day_ret,
                'leveraged_ret': leveraged_ret
            })
            
    df_turbo = pd.DataFrame(turbo_days)
    if df_turbo.empty:
        print("No Turbo Days found.")
        return

    # Find Worst Case Scenarios
    worst_day = df_turbo.loc[df_turbo['market_ret'].idxmin()]
    
    print(f"Total Turbo Days: {len(df_turbo)}")
    print(f"Worst Turbo Day Market Return: {worst_day['market_ret']*100:.2f}%")
    print(f"Worst Turbo Day Portfolio Return: {worst_day['leveraged_ret']*100:.2f}%")
    
    # Calculate Max Drawdown WITHIN a continuous Turbo Streak?
    # Approximating: Consecutive negative days with Turbo ON
    # If Market drops -3%, -3%, -3%... Turbo amplifies to -7.5%, -7.5%, -7.5%.
    # Compound that.
    
    # Check if any single day drop > 10% (Market) which would be -25% (Portfolio)
    dangerous_days = df_turbo[df_turbo['market_ret'] < -0.10]
    if not dangerous_days.empty:
        print(f"CRITICAL WARNING: Found {len(dangerous_days)} days where Market dropped >10% while Turbo was ON!")
        print(dangerous_days)
    else:
        print("Safety Check 1 Passed: No single day market drop > -10% while Turbo ON.")
        
    # Check for margin call triggers (Cumulative drop > 20% in short window during Turbo)
    # Simple check: Sort by worst market returns
    print("\nTop 5 Worst Market Days with Turbo ON:")
    print(df_turbo.sort_values('market_ret').head(5)[['date', 'market_ret', 'leveraged_ret']])

if __name__ == "__main__":
    check_turbo_risk()
