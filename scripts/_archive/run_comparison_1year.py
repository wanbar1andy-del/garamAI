import sys
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ComparisonSim")
logger.setLevel(logging.INFO)

# Add project root
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS
from garam.engine.controller import HybridController
from garam.engine.legacy import LegacyEngine
from garam.engine.advanced import AdvancedEngine

def run_comparison():
    logger.info("--- Starting 1-Year Strategy Comparison (A vs C-Lite) ---")
    
    # Define Period (Last 1 Year)
    end_date = datetime(2025, 12, 5) 
    start_date = datetime(2024, 12, 1)
    
    dates = pd.date_range(start_date, end_date, freq='B')
    logger.info(f"Period: {start_date.date()} to {end_date.date()} ({len(dates)} days)")
    
    # Load Universe & Data
    logger.info("Loading Data...")
    uni = pd.read_csv(PATHS.DATA_DIR / "real_universe_400.csv")
    targets = uni['Code'].astype(str).str.zfill(6).tolist() if 'Code' in uni.columns else []
    
    market_data = {'close': {}, 'open': {}, 'high': {}, 'low': {}, 'volume': {}}
    valid_targets = []
    
    for sym in targets:
        f = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        if f.exists():
            df = pd.read_csv(f)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            market_data['close'][sym] = df['close']
            market_data['open'][sym] = df['open']
            market_data['high'][sym] = df['high']
            market_data['low'][sym] = df['low']
            if 'volume' in df.columns:
                market_data['volume'][sym] = df['volume']
            else:
                market_data['volume'][sym] = 0
                
            valid_targets.append(sym)
            
    md_df = {k: pd.DataFrame(v) for k, v in market_data.items()}
    logger.info(f"Data Loaded for {len(valid_targets)} stocks.")
    
    # --- STRATEGY A (BASELINE / HIGH RISK) ---
    logger.info("Initializing Strategy A: Baseline Turbo (No Vol)...")
    eng1_a = LegacyEngine(use_volatility_sizing=False)
    eng2_a = AdvancedEngine(use_sentiment=True, use_volatility_timing=False)
    
    ctrl_a = HybridController() 
    ctrl_a.engine1 = eng1_a
    ctrl_a.engine2 = eng2_a
    
    # --- STRATEGY C-Lite (VOLATILITY FILTER ONLY) ---
    logger.info("Initializing Strategy C: Volatility Filter Only (No Resizing)...")
    # Note: use_volatility_filter=True, use_volatility_sizing=False
    eng1_b = LegacyEngine(use_volatility_sizing=False, use_volatility_filter=True)
    eng2_b = AdvancedEngine(use_sentiment=True, use_volatility_timing=True)
    
    ctrl_b = HybridController()
    ctrl_b.engine1 = eng1_b
    ctrl_b.engine2 = eng2_b
    
    # Variables
    results = {'A': [], 'B': []}
    
    logger.info("Starting Simulation Loop...")
    
    import time
    t0 = time.time()
    
    for d in dates:
        d_ts = pd.Timestamp(d)
        
        if d_ts not in md_df['close'].index: continue
            
        # Context (Window = 300 days)
        window_start = d_ts - timedelta(days=300)
        md_slice = {k: v.loc[window_start:d_ts].copy() for k, v in md_df.items()}
        
        context = {
            'market_data': md_slice,
            'universe': valid_targets,
            'regime': 'R3_UP_BOX' 
        }
        
        # Run A
        try:
            res_a = ctrl_a.run_cycle(d_ts, context)
            sigs_a = res_a['signals'] 
            mode_a = res_a['directives'].get('mode', 'NORMAL')
        except:
            sigs_a = {}
            mode_a = "ERROR"
            
        # Run B (Strategy C-Lite)
        try:
            res_b = ctrl_b.run_cycle(d_ts, context)
            sigs_b = res_b['signals']
            mode_b = res_b['directives'].get('mode', 'NORMAL')
        except:
            sigs_b = {}
            mode_b = "ERROR"
            
        results['A'].append({'date': d_ts, 'signals': sigs_a, 'mode': mode_a})
        results['B'].append({'date': d_ts, 'signals': sigs_b, 'mode': mode_b})
        
        if len(results['A']) % 20 == 0:
            logger.info(f"Processed {d.date()}...")
            
    # --- CALCULATE EQUITY (High Leverage) ---
    logger.info("Calculating Returns (Turbo 2.4x)...")
    
    eq_curve = []
    curr_eq_a = 100.0
    curr_eq_b = 100.0
    
    for i in range(len(results['A']) - 1):
        row_a = results['A'][i]
        row_b = results['B'][i]
        date_t = row_a['date']
        
        next_row = results['A'][i+1] # Date matches
        date_next = next_row['date']
        
        # Get Weights
        w_a = row_a['signals']
        w_b = row_b['signals']
        
        def calc_day_return(weights):
            if not weights: return 0.0
            total = sum(weights.values())
            if total == 0: return 0.0
            
            norm_weights = {k: v / total for k, v in weights.items()}
            day_pnl = 0.0
            for sym, w in norm_weights.items():
                if sym in md_df['close'].columns:
                    try:
                        p0 = md_df['close'][sym].loc[date_t]
                        p1 = md_df['close'][sym].loc[date_next]
                        ret = (p1 - p0) / p0
                        day_pnl += ret * w
                    except: pass
            return day_pnl

        dirs_a = row_a.get('mode', 'NORMAL')
        # Realistic 1.0x (No Leverage)
        # Strategy A: Pure stock selection, no margin
        mul_a = 1.0 
        
        dirs_b = row_b.get('mode', 'NORMAL')
        # Strategy C: Same 1.0x, but with volatility filter
        # Exception: If market crashes (ABS mode), reduce to 0.5x
        mul_b = 1.0 if dirs_b not in ['ABS', 'EMERGENCY'] else 0.5
        
        raw_ret_a = calc_day_return(w_a)
        raw_ret_b = calc_day_return(w_b)
        
        final_ret_a = raw_ret_a * mul_a
        final_ret_b = raw_ret_b * mul_b
        
        curr_eq_a *= (1 + final_ret_a)
        curr_eq_b *= (1 + final_ret_b)
        
        eq_curve.append({
            'date': date_next,
            'Eq_A': curr_eq_a,
            'Eq_B': curr_eq_b
        })
        
    res_df = pd.DataFrame(eq_curve)
    res_df.set_index('date', inplace=True)
    
    final_a = res_df['Eq_A'].iloc[-1]
    final_b = res_df['Eq_B'].iloc[-1]
    ret_a = (final_a - 100)
    ret_b = (final_b - 100)
    
    logger.info("--- FINAL RESULTS ---")
    logger.info(f"Strategy A (Baseline Turbo): {ret_a:.2f}%")
    logger.info(f"Strategy C (Vol Filter Lite): {ret_b:.2f}%")
    
    plt.figure(figsize=(12, 6))
    plt.plot(res_df.index, res_df['Eq_A'], label=f"Baseline (A): {ret_a:.1f}%", color='gray', linestyle='--')
    plt.plot(res_df.index, res_df['Eq_B'], label=f"Vol Filter Only (C): {ret_b:.1f}%", color='red', linewidth=2)
    plt.title("Strategy Comparison: Baseline (A) vs Vol-Filter Lite (C) [Turbo 2.4x]")
    plt.ylabel("Equity (Base 100)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    out_path = Path("C:/Users/wanba/.gemini/antigravity/brain/cd157bd2-0327-40b0-8357-ad55c78ee0e1/comparison_1year_AC.png")
    plt.savefig(out_path)
    logger.info(f"Graph Saved: {out_path}")
    
    csv_path = Path("C:/Users/wanba/.gemini/antigravity/brain/cd157bd2-0327-40b0-8357-ad55c78ee0e1/comparison_1year_AC.csv")
    res_df.to_csv(csv_path)

if __name__ == "__main__":
    run_comparison()
