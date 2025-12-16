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
    e1_path = "C:/garam/garam/simulation_1year_comparison.csv"
    if not os.path.exists(e1_path):
        # Fallback to creating it from account_snapshot if missing?
        # Or try searching
        print(f"File not found: {e1_path}, trying to locate...")
        # Assume it exists for now based on previous context
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

def run_sweep():
    print("=== Overnight Engine 2 Ratio Sweep ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # HMM Init
    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])
    
    # Ratios to test
    ratios = [0.08, 0.10, 0.12, 0.15]
    results = []
    
    for r2 in ratios:
        w2 = r2
        w1 = 1.0 - w2 # Fully Invested Assumption
        
        # Or Hybrid Assumption: w1 fixed at 0.05, rest is cash?
        # Given user said "Ratio", implies allocation.
        # Let's interpret as "W_E2 = Ratio, W_E1 = Rest" -> High Risk Setup if E1 is risky.
        
        # SIMULATION LOOP
        equity = 100_000_000.0
        peak = equity
        mdd = 0.0
        
        for date, row in df.iterrows():
            recent_data = df_full_history.loc[:date]['close'].tail(50)
            regime = hmm.predict_regime(recent_data)
            
            r_e1 = row['ret_e1']
            r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
            
            # Dynamic rules: Turbo/ABS
            curr_w1 = w1
            curr_w2 = w2
            
            if regime == 'BULL':
                curr_w2 *= 2.5 # Turbo
            elif regime == 'BEAR':
                curr_w1 *= 0.5 # ABS
            
            # Re-normalize or strict exposure?
            # Existing script normalizes:
            total_w = curr_w1 + curr_w2
            if total_w > 0:
                blended_ret = (curr_w1 * r_e1 + curr_w2 * r_e2) / total_w
            else:
                blended_ret = 0.0
                
            equity *= (1.0 + blended_ret)
            
            # MDD Calc
            if equity > peak: peak = equity
            dd = (equity - peak) / peak
            if dd < mdd: mdd = dd
            
        final_ret = (equity - 100_000_000) / 100_000_000
        results.append({
            "E2_Ratio": f"{int(r2*100)}%",
            "E1_Ratio": f"{int(w1*100)}%",
            "Total_Return": f"{final_ret*100:.2f}%",
            "MDD": f"{mdd*100:.2f}%",
            "Final_Equity": int(equity)
        })
        
    # Print Table
    res_df = pd.DataFrame(results)
    print("\n[Comparison Result]")
    print(res_df.to_string(index=False))
    
    print("\n\n=== [Scenario B] Interpreting as 'Engine 1 Ratio' (Logic Inversion) ===")
    results_b = []
    
    for r1 in ratios:
        w1 = r1
        w2 = 1.0 - w1 # E2 takes the rest (85-92%)
        
        equity = 100_000_000.0
        peak = equity
        mdd = 0.0
        
        for date, row in df.iterrows():
            recent_data = df_full_history.loc[:date]['close'].tail(50)
            regime = hmm.predict_regime(recent_data)
            
            r_e1 = row['ret_e1']
            r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
            
            curr_w1 = w1
            curr_w2 = w2
            
            if regime == 'BULL':
                curr_w2 *= 2.5
            elif regime == 'BEAR':
                curr_w1 *= 0.5
            
            total_w = curr_w1 + curr_w2
            if total_w > 0:
                blended_ret = (curr_w1 * r_e1 + curr_w2 * r_e2) / total_w
            else:
                blended_ret = 0.0
                
            equity *= (1.0 + blended_ret)
            
            if equity > peak: peak = equity
            dd = (equity - peak) / peak
            if dd < mdd: mdd = dd
            
        final_ret = (equity - 100_000_000) / 100_000_000
        results_b.append({
            "E1_Ratio (Tested)": f"{int(r1*100)}%",
            "E2_Ratio": f"{int(w2*100)}%",
            "Total_Return": f"{final_ret*100:.2f}%",
            "MDD": f"{mdd*100:.2f}%",
            "Final_Equity": int(equity)
        })
        
    res_df_b = pd.DataFrame(results_b)
    print(res_df_b.to_string(index=False))

    
if __name__ == "__main__":
    run_sweep()
