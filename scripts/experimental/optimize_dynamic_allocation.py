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

def run_optimization():
    print("=== Dynamic Allocation Optimization (Scenario B Base) ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # HMM Init
    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])
    
    # Base Safe Allocation
    BASE_E1 = 0.08
    
    # Boost Levels to Test
    boost_levels = [0.15, 0.20, 0.30, 0.40, 0.50]
    
    results = []
    
    print(f"Base Strategy: E1={int(BASE_E1*100)}% (Bull/Bear), Boost E1 in SIDEWAYS.")
    
    for boost in boost_levels:
        w1_base = BASE_E1
        w1_boost = boost
        
        equity = 100_000_000.0
        peak = equity
        mdd = 0.0
        
        regime_counts = {'BULL': 0, 'SIDEWAYS': 0, 'BEAR': 0}
        
        for date, row in df.iterrows():
            recent_data = df_full_history.loc[:date]['close'].tail(50)
            regime = hmm.predict_regime(recent_data)
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            
            r_e1 = row['ret_e1']
            r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
            
            # Dynamic Weight Logic
            if regime == 'SIDEWAYS':
                curr_w1 = w1_boost # Boost Aggressive Engine in Box
                curr_w2 = 1.0 - curr_w1
            else:
                curr_w1 = w1_base # Stay Safe in Bull/Bear
                curr_w2 = 1.0 - curr_w1
            
            blended_ret = curr_w1 * r_e1 + curr_w2 * r_e2
            equity *= (1.0 + blended_ret)
            
            if equity > peak: peak = equity
            dd = (equity - peak) / peak
            if dd < mdd: mdd = dd
            
        final_ret = (equity - 100_000_000) / 100_000_000
        
        pf_factor = final_ret / abs(mdd) if mdd != 0 else 0
        
        results.append({
            "Boost_E1_Level": f"{int(boost*100)}%",
            "Total_Return": f"{final_ret*100:.2f}%",
            "MDD": f"{mdd*100:.2f}%",
            "Profit_Factor": f"{pf_factor:.2f}",
            "Equity": int(equity)
        })
        
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    print(f"\nRegime Stats found: {regime_counts}")
    
if __name__ == "__main__":
    run_optimization()
