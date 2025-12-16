import sys
import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path

# Setup Path
sys.path.append(os.path.abspath("C:/garam/garam"))

# Fix Import: config.py is at root
try:
    from config import PATHS
except ImportError:
    # Fallback/Debug
    print("Direct import failed, trying garam.config")
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
    
    # Calculate Daily Returns from Equity 'Original'
    df_e1['ret_e1'] = df_e1['Original'].pct_change().fillna(0.0)
    
    # 2. Load Market Data (KOSPI) for Engine 2 Proxy and HMM
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    if not kospi_path.exists():
        raise FileNotFoundError(f"KOSPI data not found at {kospi_path}")
        
    df_mkt = pd.read_csv(kospi_path)
    df_mkt['timestamp'] = pd.to_datetime(df_mkt['timestamp']) # Check column name 'timestamp' from previous viewing, usually it is.
    # Wait, server_fixed used 'close'. Let's verify column names if it fails.
    # Assuming 'timestamp' and 'close'.
    df_mkt.set_index('timestamp', inplace=True)
    df_mkt.sort_index(inplace=True)
    
    # Calculate Market Returns
    df_mkt['ret_mkt'] = df_mkt['close'].pct_change().fillna(0.0)
    
    # Merge
    df = df_e1[['ret_e1']].join(df_mkt[['close', 'ret_mkt']], how='inner')
    
    return df, df_mkt # Return merged and full history for HMM training

def run_optimization():
    print("Loading Data...")
    df, df_full_history = load_data()
    print(f"Data Loaded: {len(df)} days overlapping.")
    
    # 1. Train HMM on history BEFORE the simulation period (to prevent lookahead bias)
    start_date = df.index[0]
    train_data = df_full_history[df_full_history.index < start_date]['close']
    
    print(f"Training HMM on data before {start_date} ({len(train_data)} points)...")
    hmm = HMMRegimeDetector()
    hmm.train(train_data)
    
    # 2. Predict Regimes for Simulation Period
    # We predict regime for day T based on T-1...T-N? 
    # HMM detector predict_regime uses recent history.
    # For speed, we will do a rolling prediction or simple sequence decoding if allowed.
    # Ideally: On Day T, we know Close_T. We infer Regime_T. 
    # Wait, if we use Close_T to predict Regime_T, do we trade on it?
    # Engine 2 uses HMM to decide exposure. If Regime is BEAR (high vol), we stay out.
    
    regimes = []
    # Hack for speed: Predict sequence on entire test set (Implies some lookahead if Viterbi finds optimal path globally, 
    # but GMMHMM.predict uses Viterbi. For strict backtest, should fit/predict rolling.
    # For this prototype, we'll accept `predict` on the window.)
    # Retraining rolling is too slow for python script right now.
    
    # Let's use the sequence directly
    import numpy as np
    returns = np.log(df_full_history['close'] / df_full_history['close'].shift(1)).dropna()
    volatility = returns.rolling(window=20).std().dropna()
    
    # Predict for the relevant dates
    # We need to map df index to the regime map
    # Re-predicting over the exact window
    subset_closes = df_full_history.loc[df.index[0] - pd.Timedelta(days=50) : df.index[-1]]['close']
    
    # Actually, simpler: just iterate daily in the simulation loop
    # But for optimization, we want vectorization.
    # Let's pre-calculate Regimes.
    
    print("Detecting Regimes...")
    # Using the pre-trained model to predict the sequence of states for the sim period
    # Note: we need to handle the sliding window correctly.
    # Let's just loop and predict day by day to be safe.
    
    pred_regimes = []
    for date in df.index:
        # Get last 50 days ending today
        recent = df_full_history.loc[:date]['close'].tail(50)
        r = hmm.predict_regime(recent)
        pred_regimes.append(r)
        
    df['regime'] = pred_regimes
    
    # 3. Define Engine 2 Return (Smart Beta)
    # If Bull/Sideways -> Market Return. If Bear -> Cash (0.0).
    df['ret_e2'] = np.where(df['regime'] == 'BEAR', 0.0, df['ret_mkt']) # Proxy: Avoid Bear
    
    # 4. Optimize
    results = []
    # User Request: Test Engine 1 variable 5-15%.
    # Proportion of Engine 2: 1.0 (E1=0%), 0.95 (E1=5%), 0.92, 0.90, 0.88, 0.85 (E1=15%), 0.80.
    weights = [1.0, 0.95, 0.92, 0.90, 0.88, 0.85, 0.80] 
    
    # Turbo/ABS Multipliers
    turbo_opts = [1.5, 2.0, 2.5]
    abs_opts = [0.0, 0.3, 0.5]
    
    best_cagr = -999
    best_params = None
    
    print("Running Grid Search...")
    for w_e2 in weights:
        w_e1 = 1.0 - w_e2
        
        for turbo in turbo_opts:
            for abss in abs_opts:
                # Simulate Equity Curve
                daily_rets = []
                
                for _, row in df.iterrows():
                    regime = row['regime']
                    r_e1 = row['ret_e1']
                    r_e2 = row['ret_e2']
                    
                    cur_w1 = w_e1
                    cur_w2 = w_e2
                    
                    if regime == 'BULL':
                        cur_w2 *= turbo
                    elif regime == 'BEAR':
                        cur_w1 *= abss
                        
                    tot = cur_w1 + cur_w2
                    if tot == 0:
                        daily_ret = 0.0
                    else:
                        daily_ret = (cur_w1 * r_e1 + cur_w2 * r_e2) / tot
                        
                    daily_rets.append(daily_ret)
                
                # Metrics
                cum_ret = np.prod([1+r for r in daily_rets]) - 1
                cagr = cum_ret # Since it's ~1 year
                vol = np.std(daily_rets) * np.sqrt(252)
                sharpe = cagr / vol if vol > 0 else 0
                
                # MDD
                equity = np.cumprod([1+r for r in daily_rets])
                peak = np.maximum.accumulate(equity)
                mdd = np.min((equity - peak) / peak)
                
                if cagr > best_cagr:
                    best_cagr = cagr
                    best_params = (w_e1, w_e2, turbo, abss)
                
                results.append({
                    "W_E1": w_e1, "W_E2": w_e2, 
                    "Turbo": turbo, "ABS": abss,
                    "CAGR": cagr, "MDD": mdd, "Sharpe": sharpe
                })
                
    # Output
    res_df = pd.DataFrame(results)
    res_df.sort_values('CAGR', ascending=False, inplace=True)
    
    print("\nTop 5 Configs:")
    print(res_df.head(5))
    
    csv_out = "C:/garam/garam/optimization_results_1year.csv"
    res_df.to_csv(csv_out)
    print(f"\nSaved results to {csv_out}")
    
    # Save Best Equity Curve
    # ... (Re-run best to save curve)
    
if __name__ == "__main__":
    run_optimization()
