import sys
import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path

# Setup Path
sys.path.append(os.path.abspath("C:/garam/garam"))

try:
    from config import PATHS
except ImportError:
    from garam.config import PATHS

from garam.engine.components.hmm_detector import HMMRegimeDetector

def load_data():
    # 1. Load Engine 1 (Legacy) Performance
    e1_path = "C:/garam/garam/simulation_1year_comparison.csv"
    if not os.path.exists(e1_path):
        raise FileNotFoundError(f"Engine 1 data not found at {e1_path}")
    
    df_e1 = pd.read_csv(e1_path)
    df_e1['date'] = pd.to_datetime(df_e1['date'])
    df_e1.set_index('date', inplace=True)
    df_e1['ret_e1'] = df_e1['Original'].pct_change().fillna(0.0)
    
    # 2. Load Market Data (KOSPI) for Engine 2 Proxy
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    if not kospi_path.exists():
        raise FileNotFoundError(f"KOSPI data not found at {kospi_path}")
        
    df_mkt = pd.read_csv(kospi_path)
    # Handle column names robustly
    col_map = {c: c.lower() for c in df_mkt.columns}
    df_mkt.rename(columns=col_map, inplace=True)
    
    if 'timestamp' in df_mkt.columns:
        date_col = 'timestamp'
    elif 'date' in df_mkt.columns:
        date_col = 'date'
    else:
        raise ValueError("No date column found in KOSPI csv")
        
    df_mkt[date_col] = pd.to_datetime(df_mkt[date_col])
    df_mkt.set_index(date_col, inplace=True)
    df_mkt.sort_index(inplace=True)
    
    df_mkt['ret_mkt'] = df_mkt['close'].pct_change().fillna(0.0)
    
    # Merge on overlapping dates
    df = df_e1[['ret_e1']].join(df_mkt[['close', 'ret_mkt']], how='inner')
    
    return df, df_mkt

def run_simulation():
    print("Loading Data for Dual Engine Simulation...")
    df, df_full_history = load_data()
    print(f"Simulation Period: {df.index[0].date()} to {df.index[-1].date()} ({len(df)} days)")
    
    # 1. Initialize HMM
    print("Initializing HMM Regime Detector...")
    hmm = HMMRegimeDetector()
    # Train on pre-simulation data
    start_date = df.index[0]
    train_data = df_full_history[df_full_history.index < start_date]['close']
    hmm.train(train_data)
    
    # 2. Daily Simulation Loop
    # Configuration (Golden Mix)
    W_E1 = 0.05
    W_E2 = 0.95
    TURBO = 2.5
    ABS = 0.5
    
    print(f"Configuration: E1={W_E1}, E2={W_E2}, Turbo={TURBO}, ABS={ABS}")
    
    initial_capital = 100_000_000.0
    equity = initial_capital
    
    history_records = []
    
    for date, row in df.iterrows():
        # Detect Regime (using trailing 50 days)
        recent_data = df_full_history.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        
        # Engine Returns
        r_e1 = row['ret_e1']
        
        # Engine 2 (Smart Beta): If Bear, Cash (0%). If Bull/Side, Market.
        # Note: Actually Engine 2 should probably short in Bear? 
        # User report said "avoiding bear". So Cash is correct proxy.
        r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
        
        # Dynamic Weighting
        w1 = W_E1
        w2 = W_E2
        
        active_mode = "NORMAL"
        if regime == 'BULL':
            w2 *= TURBO
            active_mode = "TURBO"
        elif regime == 'BEAR':
            w1 *= ABS
            active_mode = "ABS"
            
        # Normalize weights? 
        # In optimization we just summed: (w1*r1 + w2*r2) / (w1+w2)
        total_w = w1 + w2
        if total_w == 0:
            blended_ret = 0.0
        else:
            blended_ret = (w1 * r_e1 + w2 * r_e2) / total_w
            
        equity *= (1.0 + blended_ret)
        
        history_records.append({
            "timestamp": date,
            "total_equity": equity,
            "regime": regime,
            "mode": active_mode,
            "daily_return": blended_ret,
            "engine1_ret": r_e1,
            "engine2_ret": r_e2
        })
        
    # 3. Save Results
    res_df = pd.DataFrame(history_records)
    
    # Stats
    final_eq = res_df.iloc[-1]['total_equity']
    total_ret = (final_eq - initial_capital) / initial_capital
    cagr = total_ret # approx for 1 year
    
    mdd = 0.0
    peak = initial_capital
    for q in res_df['total_equity']:
        if q > peak: peak = q
        dd = (q - peak) / peak
        if dd < mdd: mdd = dd
        
    print(f"\nSimulation Complete.")
    print(f"Final Equity: {final_eq:,.0f} KRW")
    print(f"CAGR: {cagr*100:.2f}%")
    print(f"MDD: {mdd*100:.2f}%")
    
    # Output File for Dashboard
    # Dashboard expects timestamp, total_equity columns
    out_path = "C:/garam/garam/GARAM_Data/results/dual_engine_1y_equity.csv"
    # Ensure dir exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    res_df.to_csv(out_path, index=False)
    print(f"Saved detailed equity curve to {out_path}")
    
    # Also overwrite the account_snapshot for Dashboard visibility if requested
    # But let's keep it separate first and swap later safely
    
if __name__ == "__main__":
    run_simulation()
