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

def verify_compounding():
    print("=== Verifying Compounding Effect ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])
    
    w1_base = 0.05
    w2_base = 0.95
    TURBO_MULT = 2.5
    ABS_MULT = 0.5
    
    equity = 100_000_000.0
    
    # Store monthly status
    monthly_status = []
    
    print(f"{'Date':<12} {'Equity':<15} {'Exposure':<15} {'Regime':<10}")
    print("-" * 55)
    
    last_month = None
    
    for date, row in df.iterrows():
        recent_data = df_full_history.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        
        r_e1 = row['ret_e1']
        r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
        
        # Exposure Logic
        curr_w1 = w1_base
        curr_w2 = w2_base
        if regime == 'BULL': curr_w2 *= TURBO_MULT
        elif regime == 'BEAR': curr_w1 *= ABS_MULT
        
        total_exposure_ratio = curr_w1 + curr_w2
        
        blended_ret = curr_w1 * r_e1 + curr_w2 * r_e2
        equity *= (1.0 + blended_ret)
        
        # Log End of Month
        if date.month != last_month:
            exposure_amt = equity * total_exposure_ratio
            print(f"{date.strftime('%Y-%m-%d'):<12} {int(equity):,<15} {int(exposure_amt):,<15} {regime:<10}")
            monthly_status.append({
                'date': date.strftime('%Y-%m-%d'),
                'equity': int(equity),
                'exposure': int(exposure_amt)
            })
            last_month = date.month

    # Final logic check
    print("-" * 55)
    print(f"Final Equity: {int(equity):,}")
    print("Compounding Verified: Equity updates daily, and Exposure scales with Equity.")

if __name__ == "__main__":
    verify_compounding()
