import sys
import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MixStudy")
logger.setLevel(logging.INFO)

# Add project root
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS
from garam.engine.controller import HybridController
from garam.engine.legacy import LegacyEngine
from garam.engine.advanced import AdvancedEngine

def run_mix_study():
    logger.info("--- Starting Strategy Mix Study (B vs A Blends) ---")
    
    # 1. Configuration
    start_capital = 100_000_000.0 # 100M KRW
    start_date = datetime(2024, 12, 1)
    end_date = datetime(2025, 12, 5) # 1 Year
    
    dates = pd.date_range(start_date, end_date, freq='B')
    logger.info(f"Period: {start_date.date()} to {end_date.date()} ({len(dates)} days)")

    # 2. Initialize Engines
    # Strategy A: Baseline (Aggressive, No Vol)
    # Strategy B: Volatility (Defensive, Vol Sizing + Timing)
    
    logger.info("Initializing Strategies...")
    
    # Engine A
    eng1_a = LegacyEngine(use_volatility_sizing=False)
    eng2_a = AdvancedEngine(use_sentiment=True, use_volatility_timing=False)
    ctrl_a = HybridController()
    ctrl_a.engine1 = eng1_a
    ctrl_a.engine2 = eng2_a
    
    # Engine B
    eng1_b = LegacyEngine(use_volatility_sizing=True)
    eng2_b = AdvancedEngine(use_sentiment=True, use_volatility_timing=True)
    ctrl_b = HybridController()
    ctrl_b.engine1 = eng1_b
    ctrl_b.engine2 = eng2_b
    
    # 3. Load Data
    logger.info("Loading Market Data...")
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
            market_data['volume'][sym] = df.get('volume', 0)
            valid_targets.append(sym)
            
    md_df = {k: pd.DataFrame(v) for k, v in market_data.items()}
    logger.info(f"Loaded {len(valid_targets)} stocks.")
    
    # 4. Simulation Loop (Generate Returns for A and B)
    # We will record daily % return for A and B separately.
    
    returns_a = []
    returns_b = []
    
    # Optimization: To avoid re-running slow logic, we use vectorized checks where possible, 
    # but HybridController logic is complex. We must run the loop.
    # To speed up, we avoid re-creating dataframes excessively.
    
    logger.info("Running Simulation Loop...")
    
    # Pre-slice data for fallback optimizer?
    # No, fallback handles it.
    
    sim_results = []
    
    for i, d in enumerate(dates):
        if i % 20 == 0: logger.info(f"Processing {d.date()}...")
        
        d_ts = pd.Timestamp(d)
        if d_ts not in md_df['close'].index: continue
        
        # Context Window (Last 300 days)
        window_start = d_ts - timedelta(days=400)
        md_slice = {k: v.loc[window_start:d_ts] for k, v in md_df.items()}
        
        context = {
            'market_data': md_slice,
            'universe': valid_targets,
            'regime': 'R3_UP_BOX'
        }
        
        # Generate Signals A
        # A has No Vol, so Size Multiplier is usually 1.0 or 1.5 (Turbo).
        # We need to know NEXT DAY return to apply today's decision.
        
        # Get Return for T+1
        # Find next trading date
        next_idx = md_df['close'].index.searchsorted(d_ts) + 1
        if next_idx >= len(md_df['close'].index): break
        next_date = md_df['close'].index[next_idx]
        
        # Calculate Forward Return vector for all stocks
        # Ret = (Close_Next - Close_T) / Close_T
        p0 = md_df['close'].loc[d_ts]
        p1 = md_df['close'].loc[next_date]
        day_stock_rets = (p1 - p0) / p0
        
        # Function to run engine and get portfolio return
        def get_strat_ret(ctrl):
            try:
                res = ctrl.run_cycle(d_ts, context)
                sigs = res['signals'] # {sym: score}
                mode = res['directives'].get('mode', 'NORMAL')
                
                # Determine Size Multiplier
                # A: Baseline (VolT=False) -> If Sentiment Bad -> ABS?
                # B: Vol     (VolT=True)  -> If Vol Panic   -> ABS
                # The logic is inside AdvancedEngine. But we just check mode here.
                
                mul = 1.0
                if mode == 'TURBO': mul = 1.5
                elif mode == 'ABS' or mode == 'EMERGENCY': mul = 0.5
                
                if not sigs: return 0.0
                
                # Normalize weights to 1.0 (Base Exposure)
                total = sum(sigs.values())
                if total == 0: return 0.0
                weights = {k: v/total for k, v in sigs.items()}
                
                # Calculate Raw Return (Invested Portion)
                raw_ret = 0.0
                for sym, w in weights.items():
                    if sym in day_stock_rets:
                        r = day_stock_rets[sym]
                        if pd.notna(r):
                            raw_ret += r * w
                            
                # Apply Leverage/Brake
                final_ret = raw_ret * mul
                return final_ret
                
            except Exception as e:
                # logger.error(f"Error {d.date()}: {e}")
                return 0.0

        # Run A & B
        ret_a = get_strat_ret(ctrl_a)
        ret_b = get_strat_ret(ctrl_b)
        
        sim_results.append({
            'date': next_date,
            'ret_a': ret_a,
            'ret_b': ret_b
        })
        
    results_df = pd.DataFrame(sim_results).set_index('date')
    
    # 5. Calculate Blends
    # Cases: B 100%, B 80%, B 60%, B 40%, (and B 0% i.e. A 100%)
    
    # We blend returns daily.
    # Mix 80% B = 0.8 * Ret_B + 0.2 * Ret_A
    # This assumes daily rebalancing to fixed ratio.
    
    logger.info("Calculating Blended Equity Curves...")
    
    df = results_df.copy()
    
    df['Mix_100B'] = df['ret_b']
    df['Mix_80B']  = 0.8 * df['ret_b'] + 0.2 * df['ret_a']
    df['Mix_60B']  = 0.6 * df['ret_b'] + 0.4 * df['ret_a']
    df['Mix_40B']  = 0.4 * df['ret_b'] + 0.6 * df['ret_a']
    df['Mix_0B']   = df['ret_a'] # 100% A
    
    # Compounding
    eq_curves = {}
    final_values = {}
    
    for col in ['Mix_100B', 'Mix_80B', 'Mix_60B', 'Mix_40B', 'Mix_0B']:
        # Cumprod
        # (1+r).cumprod() * Start
        eq = (1 + df[col]).cumprod() * start_capital
        eq_curves[col] = eq
        final_values[col] = eq.iloc[-1]
        
    # 6. Reporting
    logger.info("--- FINAL RESULTS (KRW) ---")
    labels = {
        'Mix_100B': 'B 100% (Vol Optimized)',
        'Mix_80B':  'B 80% / A 20%',
        'Mix_60B':  'B 60% / A 40%',
        'Mix_40B':  'B 40% / A 60%',
        'Mix_0B':   'A 100% (Momentum)'
    }
    
    colors = {
        'Mix_100B': '#2ecc71', # Green
        'Mix_80B':  '#3498db', # Blue
        'Mix_60B':  '#9b59b6', # Purple
        'Mix_40B':  '#e67e22', # Orange
        'Mix_0B':   '#e74c3c'  # Red
    }
    
    for k, v in final_values.items():
        roi = (v - start_capital) / start_capital * 100.0
        logger.info(f"{labels[k]}: {v:,.0f} KRW ({roi:+.2f}%)")
        
    # 7. Plotting
    plt.figure(figsize=(12, 7))
    
    for col in ['Mix_100B', 'Mix_80B', 'Mix_60B', 'Mix_40B', 'Mix_0B']:
        series = eq_curves[col]
        final_v = final_values[col]
        roi = (final_v - start_capital) / start_capital * 100.0
        label_txt = f"{labels[col]} | {final_v/1000000:,.0f}M ({roi:+.1f}%)"
        
        plt.plot(series.index, series, label=label_txt, color=colors[col], linewidth=2.5 if '100B' in col or '0B' in col else 1.5)
        
    plt.title("Strategy Mix Study: Volatility (B) vs Momentum (A) | 1-Year Turbo Mode", fontsize=14)
    plt.ylabel("Equity (KRW)", fontsize=12)
    plt.xlabel("Date")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Format Y axis
    current_values = plt.gca().get_yticks()
    plt.gca().set_yticklabels(['{:,.0f}'.format(x) for x in current_values])

    out_path = Path("C:/Users/wanba/.gemini/antigravity/brain/cd157bd2-0327-40b0-8357-ad55c78ee0e1/mix_study_results.png")
    plt.savefig(out_path)
    logger.info(f"Graph Saved: {out_path}")
    
    # Save CSV
    csv_path = Path("C:/Users/wanba/.gemini/antigravity/brain/cd157bd2-0327-40b0-8357-ad55c78ee0e1/mix_study_data.csv")
    df.to_csv(csv_path)

if __name__ == "__main__":
    run_mix_study()
