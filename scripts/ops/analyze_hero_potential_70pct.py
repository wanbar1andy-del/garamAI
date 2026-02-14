"""
Hero 5-Day Potential Analysis
Purpose: 
    1. Quantify the 'Max Possible Return' (MFE) of Hero stocks over a 5-day holding period.
    2. Test the feasibility of capturing '70% of Probable Max Return'.
    3. Simulate a 5-Slot Portfolio to check risk/diversification benefits.

Logic:
    - Load 60-day data.
    - Identify Daily Hero (Top 1 Score).
    - For each Hero:
        - Track High/Low/Close for T+1 to T+5.
        - Metric 1: Max Return 5d ( (Highest High - Entry) / Entry ).
        - Metric 2: Min Drawdown 5d ( (Lowest Low - Entry) / Entry ).
        - Metric 3: 'Ideal 70% Capture' PnL (Exit at 0.7 * Max Return).
    - Portfolio Simulation (Simplified):
        - Max 5 Slots.
        - FIFO Allocation.
        - Exit Rule options to test:
            A: Fixed Profit Target (Median of Max Return * 0.7).
            B: Trailing Stop (High - Delta).
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm
import logging
from datetime import datetime
import sys

# Setup
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Data Path
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
OUT_DIR = PROJECT_ROOT / "logs/ops/hero_5d_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def process_data():
    files = list(DATA_DIR.glob("*.csv"))
    all_rows = []
    
    print(f"Loading {len(files)} files...")
    for f in tqdm(files):
        try:
            df = pd.read_csv(f)
            # Normalize Headers
            if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
            elif 'Date' in df.columns: df.rename(columns={'Date':'date'}, inplace=True)
            
            # Daily Agg
            df['day'] = df['date'].astype(str).str.slice(0, 10)
            g = df.groupby('day')
            daily = g.agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).reset_index()
            daily.rename(columns={'day': 'date'}, inplace=True)
            daily['ticker'] = f.stem
            all_rows.append(daily)
        except: pass

    big_df = pd.concat(all_rows, ignore_index=True)
    big_df['date'] = pd.to_datetime(big_df['date'])
    big_df = big_df.sort_values(['ticker', 'date'])
    
    # Feature Engineering (Score)
    # Simple vector calc for speed
    print("Calculating Scores...")
    out_dfs = []
    for tkr, sub in tqdm(big_df.groupby('ticker')):
        sub = sub.copy()
        # Ensure numeric
        c = sub['close']
        v = sub['volume']
        r5 = c.pct_change(5).fillna(0)
        r20 = c.pct_change(20).fillna(0)
        v_avg = v.rolling(20).mean()
        v_spike = (v / (v_avg + 1e-9)).fillna(0).clip(upper=3.0)
        
        erc = c * (1.0 + r20 + r5 * v_spike)
        rr = c / (erc + 1e-12)
        score = (r5 * v_spike) * (1.0 - (rr - 0.5).abs())
        sub['score'] = score
        out_dfs.append(sub)
        
    full_df = pd.concat(out_dfs).sort_values('date')
    return full_df

def analyze_potential(full_df):
    dates = sorted(full_df['date'].unique())
    heroes = []
    
    print("Selecting Heroes and Analyzing 5-Day Paths...")
    for d in dates:
        day_stats = full_df[full_df['date'] == d]
        cand = day_stats[day_stats['score'] > 0]
        if not cand.empty:
            best = cand.loc[cand['score'].idxmax()]
            
            # Future Path (T+1 to T+5)
            tkr = best['ticker']
            future = full_df[ (full_df['ticker'] == tkr) & (full_df['date'] > d) ].head(5)
            
            if not future.empty:
                entry_px = best['close'] # Buy at score-day close
                max_high = future['high'].max()
                min_low = future['low'].min()
                
                max_ret = (max_high - entry_px) / entry_px
                max_dd = (min_low - entry_px) / entry_px
                
                # Close at T+5 (or last avail)
                final_px = future.iloc[-1]['close']
                final_ret = (final_px - entry_px) / entry_px
                
                heroes.append({
                    'date': d,
                    'ticker': tkr,
                    'entry': entry_px,
                    'max_ret_5d': max_ret,
                    'max_dd_5d': max_dd,
                    'final_ret_5d': final_ret,
                    'days_held': len(future)
                })
    
    if not heroes: return pd.DataFrame()
    return pd.DataFrame(heroes)

def simulate_portfolio(heroes_df, full_df):
    # Simulate 5-Slot Portfolio Strategy
    # Strategy: 
    #   - Enter Hero at Close
    #   - Exit Target: 70% of the "Expected Max Return" (Dynamic) OR Fixed Target?
    #   - Let's test a "Smart Target": 
    #     The user wants to "capture 70% of the max possible". 
    #     Since we don't know the future max, we use statistics.
    #     If avg max return is X%, we target 0.7 * X%.
    
    avg_max_pot = heroes_df['max_ret_5d'].median()
    target_return = avg_max_pot * 0.7
    
    print(f"\n--- Strategy Parameter ---")
    print(f"Median 5-Day Max Potential: {avg_max_pot*100:.2f}%")
    print(f"Target Profit (70% capture): {target_return*100:.2f}%")
    print(f"Stop Loss (Fixed): -10% (assumption)")
    
    # Run Simulation
    # We need day-by-day loop again? 
    # Actually, we can just process the "heroes_df" if we assume we always take the signal.
    # But w/ 5 slots, we might skip some if full.
    
    # Let's do a simple count check
    # Max active positions per day
    # This is a bit complex to hack in 1 file without full event loop.
    # Let's approximate: 
    # Win Rate of this "Target Strategy":
    # If max_ret_5d > target -> WIN (Exit at target)
    # Else if max_dd_5d < -0.10 -> LOSS (Exit at -10%)
    # Else -> CLOSE at T+5 (final_ret)
    
    results = []
    
    for _, row in heroes_df.iterrows():
        outcome = 0.0
        
        # Check stops/targets
        # We don't have intraday granularity here (only daily High/Low)
        # Assume High happens before Low on bull candles? No, conservative:
        # If Low hits SL, we die. If High hits TP, we win.
        # If both hit on same day? Assume Loss (Conservative).
        
        # For this Daily-level analysis, we just check likelihood.
        hit_tp = row['max_ret_5d'] >= target_return
        hit_sl = row['max_dd_5d'] <= -0.10
        
        if hit_sl and not hit_tp:
            outcome = -0.10
        elif hit_tp and not hit_sl:
            outcome = target_return
        elif hit_tp and hit_sl:
            # Both hit. Whipsaw. Assume Loss 50% / Win 50% or Loss.
            outcome = -0.10 # Conservative catch
        else:
            # Neither hit. Time Stop.
            outcome = row['final_ret_5d']
            
        results.append(outcome)
        
    return pd.Series(results), target_return

def main():
    df = process_data()
    heroes = analyze_potential(df)
    
    if heroes.empty:
        print("No heroes found.")
        return

    # Stats
    print("\n--- Hero 5-Day Potential Analysis ---")
    print(f"Total Heroes: {len(heroes)}")
    print(f"Avg Max Return (5d): {heroes['max_ret_5d'].mean()*100:.2f}%")
    print(f"Median Max Return (5d): {heroes['max_ret_5d'].median()*100:.2f}%")
    print(f"Avg Max Drawdown (5d): {heroes['max_dd_5d'].mean()*100:.2f}%")
    
    # Potential Tiers
    reach_10 = (heroes['max_ret_5d'] >= 0.10).mean()
    reach_20 = (heroes['max_ret_5d'] >= 0.20).mean()
    print(f"Reach >= 10%: {reach_10*100:.1f}%")
    print(f"Reach >= 20%: {reach_20*100:.1f}%")
    
    # Strategy Sim
    pnl_series, target = simulate_portfolio(heroes, df)
    
    win_rate = (pnl_series > 0).mean()
    avg_pnl = pnl_series.mean()
    total_ret = pnl_series.sum() # Simple sum of returns (uncompounded)
    
    print(f"\n--- '70% Capture' Strategy Sim (Target: {target*100:.1f}%) ---")
    print(f"Win Rate: {win_rate*100:.1f}%")
    print(f"Avg PnL per Trade: {avg_pnl*100:.2f}%")
    print(f"Total Return (Sum): {total_ret*100:.2f}% (over 60 days, 1 slot equivalent)")
    
    # Recommendations
    rec = f"""
    [Analysis Result]
    1. Hero stocks typically reach a MAX height of {heroes['max_ret_5d'].median()*100:.1f}% in 5 days.
    2. Therefore, a "70% Capture" target would be approx +{(heroes['max_ret_5d'].median()*0.7)*100:.1f}%.
    3. If we set TP at this level and SL at -10%, the estimated Win Rate is {win_rate*100:.1f}%.
    4. 5-Slot Expansion: With {len(heroes)} signals over 60 days, avg {len(heroes)/60:.1f} per day.
       5 slots are sufficient to take ALL signals.
    """
    print(rec)
    
    # Save
    heroes.to_csv(OUT_DIR / "hero_potential_stats.csv")
    (OUT_DIR / "summary.txt").write_text(rec, encoding='utf-8')

if __name__ == "__main__":
    main()
