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
    
    # Inner Join
    df = df_e1[['ret_e1']].join(df_mkt[['close', 'ret_mkt']], how='inner')
    return df, df_mkt

def run_simulation():
    print("=== Final Verification: Scenario B vs Alternatives ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # HMM Init
    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])
    
    # Configs
    scenarios = [
        {"name": "Scenario A (High Risk)", "w1": 0.92, "w2": 0.08},
        {"name": "Scenario B (Golden)",   "w1": 0.08, "w2": 0.92},
        {"name": "Original (Conservative)", "w1": 0.05, "w2": 0.95}
    ]
    
    CRASH_DATE = pd.Timestamp("2025-03-24")
    
    results = []
    
    for sc in scenarios:
        w1_fixed = sc['w1']
        w2_fixed = sc['w2']
        
        equity = 100_000_000.0
        peak = equity
        mdd = 0.0
        
        crash_day_loss = 0.0
        
        for date, row in df.iterrows():
            recent_data = df_full_history.loc[:date]['close'].tail(50)
            regime = hmm.predict_regime(recent_data)
            
            r_e1 = row['ret_e1']
            r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
            
            # Dynamic Logic is DISABLED (Fixed Allocation as proved best)
            curr_w1 = w1_fixed
            curr_w2 = w2_fixed
            
            # Turbo/ABS also DISABLED for Fixed Test (Unless user implies Dynamic rules active?)
            # "Scenario B fixed" implies static weights?
            # User said "Scenario B Fixed". But originally code had Turbo/ABS.
            # Let's KEEP Turbo/ABS relative to the weights to be consistent with "Scenario B" definition in code?
            # Script `run_dual_engine_1y_detailed.py` had Turbo/ABS.
            # If I disable them, results might differ from previous 64%.
            # Comparison B in `sweep_engine2.py` INCLUDED Turbo/ABS logic.
            # So I MUST include them here to match the 64% result.
            
            if regime == 'BULL':
                # Turbo Logic: Boost E2 (Wait, original logic boosted E2 in Bull?)
                # In `sweep_engine2.py`:
                # if regime == 'BULL': curr_w2 *= 2.5
                # if regime == 'BEAR': curr_w1 *= 0.5
                curr_w2 *= 2.5
            elif regime == 'BEAR':
                curr_w1 *= 0.5
                
            # Normalize
            total_w = curr_w1 + curr_w2
            if total_w > 0:
                blended_ret = (curr_w1 * r_e1 + curr_w2 * r_e2) / total_w
            else:
                blended_ret = 0.0
                
            equity *= (1.0 + blended_ret)
            
            if date.date() == CRASH_DATE.date():
                crash_day_loss = blended_ret
            
            if equity > peak: peak = equity
            dd = (equity - peak) / peak
            if dd < mdd: mdd = dd
            
        final_ret = (equity - 100_000_000) / 100_000_000
        profit = equity - 100_000_000
        
        results.append({
            "Scenario": sc['name'],
            "Total_Return": f"{final_ret*100:.2f}%",
            "Profit_KRW": f"{int(profit):,}",
            "MDD": f"{mdd*100:.2f}%",
            "Crash_Day_Loss": f"{crash_day_loss*100:.2f}%"
        })
        
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    
if __name__ == "__main__":
    run_simulation()
