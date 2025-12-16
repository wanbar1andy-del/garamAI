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

def calc_deployment():
    print("=== Calculating Average Capital Deployment Rate ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # User Settings (Dynamic Turbo)
    W1_BASE = 0.05
    W2_BASE = 0.95
    TURBO_MULT = 2.5
    ABS_MULT = 0.5
    
    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])
    
    daily_exposures = []
    
    regime_counts = {'BULL': 0, 'SIDEWAYS': 0, 'BEAR': 0}
    
    for date, row in df.iterrows():
        recent_data = df_full_history.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        # Calculate Exposure
        w1 = W1_BASE
        w2 = W2_BASE
        
        current_exposure = 0.0
        
        if regime == 'BULL':
            # Turbo On: E2 boosted
            w2_deployed = w2 * TURBO_MULT
            w1_deployed = w1
            # E2 is Investment, E1 is Investment
            current_exposure = w1_deployed + w2_deployed
            
        elif regime == 'SIDEWAYS':
            # Normal: E1 + E2
            current_exposure = w1 + w2
            
        elif regime == 'BEAR':
            # Bear: E1 reduced, E2 is CASH (0% Exposure)
            w1_deployed = w1 * ABS_MULT
            w2_deployed = 0.0 # Cash
            current_exposure = w1_deployed + w2_deployed
        
        daily_exposures.append(current_exposure)
        
    avg_exposure = np.mean(daily_exposures)
    max_exposure = np.max(daily_exposures)
    min_exposure = np.min(daily_exposures)
    
    # Calculate Regime Percentages
    total_days = len(daily_exposures)
    bull_pct = regime_counts['BULL'] / total_days * 100
    side_pct = regime_counts['SIDEWAYS'] / total_days * 100
    bear_pct = regime_counts['BEAR'] / total_days * 100
    
    print(f"Days Analyzed: {total_days}")
    print(f"Average Capital Deployment Rate: {avg_exposure*100:.2f}%")
    print(f"Max Deployment: {max_exposure*100:.2f}% (Bull with Turbo)")
    print(f"Min Deployment: {min_exposure*100:.2f}% (Bear with ABS)")
    print(f"Regime Dist: Bull {bull_count} ({bull_pct:.1f}%), Side {side_pct:.1f}%, Bear {bear_pct:.1f}%")

if __name__ == "__main__":
    calc_deployment()
