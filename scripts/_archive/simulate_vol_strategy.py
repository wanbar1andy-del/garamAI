import sys
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

START_DATE = "2025-10-01"
END_DATE = "2025-11-24"
INITIAL_CAPITAL = 100.0

def run_simulation():
    print(f"--- VOLATILITY STRATEGY SIMULATION ({START_DATE} ~ {END_DATE}) ---")
    
    # 1. Load Factor Data
    print("Loading factor data...")
    factor_dir = PATHS.DATA_DIR / "factors"
    factor_files = list(factor_dir.glob("*_volf.csv"))
    
    data_panel = {} # {symbol: daily_df}
    
    for f in factor_files:
        sym = f.stem.replace("_volf", "")
        df = pd.read_csv(f)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        # Filter period
        period_df = df.loc[START_DATE:END_DATE]
        if not period_df.empty:
            # Shift returns: Decision today uses today's Close, result is tomorrow's Close
            # We calculate return from Today Close to Tomorrow Close
            period_df['next_ret'] = period_df['close'].pct_change().shift(-1)
            data_panel[sym] = period_df
            
    dates = sorted(list(set([d for sym in data_panel for d in data_panel[sym].index])))
    dates = [d for d in dates if d < pd.Timestamp(END_DATE)] # Stop one day early for next_ret
    
    # Strategy States
    eq_plain = INITIAL_CAPITAL
    eq_quality = INITIAL_CAPITAL
    eq_riskpar = INITIAL_CAPITAL
    
    hist_plain = []
    hist_quality = []
    hist_riskpar = []

    print(f"\n{'Date':<10} | {'Plain':<8} | {'Quality':<8} | {'RiskParity':<10}")
    print("-" * 50)

    for d in dates:
        # Gather Universe for Today
        candidates = []
        for sym, df in data_panel.items():
            if d in df.index:
                row = df.loc[d]
                # Filter: No NANs
                if pd.notna(row['ret_6m']) and pd.notna(row['quality_score']) and pd.notna(row['atr_pct']):
                     candidates.append({
                         'sym': sym,
                         'ret_6m': row['ret_6m'],
                         'quality_score': row['quality_score'],
                         'atr_pct': row['atr_pct'],
                         'vol_accel': row['vol_accel'],
                         'next_ret': row['next_ret']
                     })
        
        if not candidates: continue
        
        # --- Strategy A: Plain Momentum ---
        # Top 5 by ret_6m
        candidates.sort(key=lambda x: x['ret_6m'], reverse=True)
        top5_plain = candidates[:5]
        
        # Determine Weights (Equal)
        ret_plain = 0
        if top5_plain:
            try:
                mean_ret = np.mean([c['next_ret'] for c in top5_plain if pd.notna(c['next_ret'])])
                if pd.notna(mean_ret): ret_plain = mean_ret
            except: pass
            
        # --- Strategy B: Quality Momentum ---
        # Top 5 by quality_score (Risk Adjusted)
        candidates.sort(key=lambda x: x['quality_score'], reverse=True)
        top5_quality = candidates[:5]
        
        ret_quality = 0
        if top5_quality:
            try:
                mean_ret = np.mean([c['next_ret'] for c in top5_quality if pd.notna(c['next_ret'])])
                if pd.notna(mean_ret): ret_quality = mean_ret
            except: pass

        # --- Strategy C: Risk Parity Sizing ---
        # Use PLAIN Selection (Top 5 by ret_6m) BUT Weight by 1/ATR
        # (Compare 'Sizing Effect' only)
        candidates.sort(key=lambda x: x['ret_6m'], reverse=True)
        top5_risk = candidates[:5]
        
        ret_riskpar = 0
        if top5_risk:
            inv_atrs = [(1/(c['atr_pct'] if c['atr_pct']>0 else 1)) for c in top5_risk]
            total_inv = sum(inv_atrs)
            if total_inv > 0:
                weights = [ia/total_inv for ia in inv_atrs]
                rets = [c['next_ret'] for c in top5_risk]
                # Weighted Sum
                # Handle NaNs in next_ret (assume 0 if missing)
                weighted_ret = sum([w * (r if pd.notna(r) else 0) for w, r in zip(weights, rets)])
                ret_riskpar = weighted_ret
                
        # Update Equity
        eq_plain *= (1 + ret_plain)
        eq_quality *= (1 + ret_quality)
        eq_riskpar *= (1 + ret_riskpar)
        
        d_str = d.strftime("%Y-%m-%d")
        print(f"{d_str:<10} | {eq_plain:>8.1f} | {eq_quality:>8.1f} | {eq_riskpar:>10.1f}")
        
        hist_plain.append({'date': d, 'equity': eq_plain})
        hist_quality.append({'date': d, 'equity': eq_quality})
        hist_riskpar.append({'date': d, 'equity': eq_riskpar})

    # Summary
    print("-" * 50)
    print("Final Results:")
    print(f"1. Plain Momentum (Basis): {eq_plain:.2f} ({(eq_plain-INITIAL_CAPITAL):.2f}%)")
    print(f"2. Quality Momentum (Rank): {eq_quality:.2f} ({(eq_quality-INITIAL_CAPITAL):.2f}%)")
    print(f"3. Risk Parity (Allocation): {eq_riskpar:.2f} ({(eq_riskpar-INITIAL_CAPITAL):.2f}%)")
    
    # Save Results
    pd.DataFrame(hist_plain).to_csv(PATHS.DATA_DIR / "sim_plain.csv")
    pd.DataFrame(hist_quality).to_csv(PATHS.DATA_DIR / "sim_quality.csv")
    pd.DataFrame(hist_riskpar).to_csv(PATHS.DATA_DIR / "sim_riskpar.csv")

if __name__ == "__main__":
    run_simulation()
