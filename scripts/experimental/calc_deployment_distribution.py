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
    e1_path = "C:/garam/garam/simulation_1year_comparison.csv"
    if not os.path.exists(e1_path):
        raise FileNotFoundError(f"Engine 1 data not found at {e1_path}")
    
    df_e1 = pd.read_csv(e1_path)
    df_e1['date'] = pd.to_datetime(df_e1['date'])
    df_e1.set_index('date', inplace=True)
    df_e1['ret_e1'] = df_e1['Original'].pct_change().fillna(0.0)
    
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    df_mkt = pd.read_csv(kospi_path)
    col_map = {c: c.lower() for c in df_mkt.columns}
    df_mkt.rename(columns=col_map, inplace=True)
    date_col = 'timestamp' if 'timestamp' in df_mkt.columns else 'date'
    df_mkt[date_col] = pd.to_datetime(df_mkt[date_col])
    df_mkt.set_index(date_col, inplace=True)
    df_mkt.sort_index(inplace=True)
    df_mkt['ret_mkt'] = df_mkt['close'].pct_change().fillna(0.0)
    
    df = df_e1[['ret_e1']].join(df_mkt[['close', 'ret_mkt']], how='inner')
    return df, df_mkt

def calc_distribution():
    print("=== Calculating Deployment Distribution ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])
    
    counts = {'TURBO_242': 0, 'NORMAL_100': 0, 'SAFE_2': 0}
    total_days = 0
    
    for date, row in df.iterrows():
        recent_data = df_full_history.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        total_days += 1
        
        if regime == 'BULL':
            counts['TURBO_242'] += 1
        elif regime == 'SIDEWAYS':
            counts['NORMAL_100'] += 1
        elif regime == 'BEAR':
            counts['SAFE_2'] += 1
            
    print(f"Total Trading Days: {total_days}")
    print(f"1. Maximum Deployment (242.5%): {counts['TURBO_242']} days ({(counts['TURBO_242']/total_days)*100:.1f}%)")
    print(f"2. Normal Deployment (100.0%):  {counts['NORMAL_100']} days ({(counts['NORMAL_100']/total_days)*100:.1f}%)")
    print(f"3. Minimum Deployment (2.5%):   {counts['SAFE_2']} days ({(counts['SAFE_2']/total_days)*100:.1f}%)")

if __name__ == "__main__":
    calc_distribution()
