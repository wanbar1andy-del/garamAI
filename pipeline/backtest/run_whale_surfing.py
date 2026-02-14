import pandas as pd
import numpy as np
import sys
from pathlib import Path
from run_alpha_robust import load_data

def analyze_whale_surfing():
    print("::: WHALE SURFING STRATEGY RESEARCH :::")
    print("Objective: Find optimal entry TACTIC after Whale Strike detection.")
    print("Tactics: 1. Instant (Ride), 2. Pullback (Wait), 3. Breakout (Confirm)")
    
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    closes, volumes = load_data(data_dir, "universe.csv", "20250601", "20251212")
    
    results = []
    
    for sym in closes.columns:
        c = closes[sym].dropna()
        v = volumes[sym].reindex(c.index).fillna(0)
        
        if c.empty: continue
        
        # 1. Detect Whale Strike (The Wave)
        # Vol > 5x MA20 AND Price > 1.5% (Strong Impulse)
        v_ma20 = v.rolling(window=20).mean()
        vol_ratio = v / (v_ma20 + 1e-9)
        ret = c.pct_change()
        
        is_strike = (vol_ratio > 5.0) & (ret > 0.015)
        
        strike_indices = is_strike[is_strike].index
        
        for ts in strike_indices:
            try:
                loc = c.index.get_loc(ts)
                if loc + 60 >= len(c): continue # Need future data
                
                strike_close = c.iloc[loc]
                strike_high = c.iloc[loc] # Approximation (using Close as High for minute)
                
                # --- Tactic 1: Instant Entry (The Tail) ---
                # Enter at Close of Strike Bar
                entry_1 = strike_close
                
                # --- Tactic 2: Pullback Entry (The Belly) ---
                # Valid if price drops -0.5% ~ -1.5% within next 5 mins
                # If not, no entry (Missed)
                future_window = c.iloc[loc+1:loc+6]
                pullback_target = strike_close * 0.995
                filled_mask = future_window <= pullback_target
                
                if filled_mask.any():
                    # Entered at Limit Price
                    entry_2 = pullback_target
                    entry_time_2 = filled_mask.idxmax() # First hit
                    loc_2 = c.index.get_loc(entry_time_2)
                else:
                    entry_2 = None # Missed trade
                    loc_2 = loc
                
                # --- Tactic 3: Breakout Confirmation (The Head) ---
                # Valid if price exceeds Strike High within next 10 mins
                # Buy Stop at High
                breakout_window = c.iloc[loc+1:loc+11]
                breakout_target = strike_high * 1.001
                breakout_mask = breakout_window >= breakout_target
                
                if breakout_mask.any():
                    entry_3 = breakout_target
                    entry_time_3 = breakout_mask.idxmax()
                    loc_3 = c.index.get_loc(entry_time_3)
                else:
                    entry_3 = None
                    loc_3 = loc
                    
                # --- Measure Outcomes (ROI) ---
                # Horizon: 30 mins after Strike
                exit_price = c.iloc[loc + 30]
                
                # Result 1
                res_1 = (exit_price / entry_1) - 1.0
                
                # Result 2
                res_2 = (exit_price / entry_2) - 1.0 if entry_2 else np.nan
                
                # Result 3
                res_3 = (exit_price / entry_3) - 1.0 if entry_3 else np.nan
                
                results.append({
                    "sym": sym,
                    "ts": ts,
                    "vol_ratio": vol_ratio.loc[ts],
                    "instant_roi": res_1,
                    "pullback_roi": res_2,
                    "breakout_roi": res_3,
                    "pullback_filled": (entry_2 is not None),
                    "breakout_filled": (entry_3 is not None)
                })
                
            except Exception as e:
                continue

    # Analysis
    df = pd.DataFrame(results)
    print("\n" + "="*60)
    print(f"🐋 WHALE SURFING RESULTS (Events: {len(df)})")
    print("="*60)
    
    # 1. Instant
    win_1 = (df['instant_roi'] > 0).mean() * 100
    avg_1 = df['instant_roi'].mean() * 100
    print(f"[TACTIC 1: Instant] Win Rate: {win_1:.1f}% | Avg ROI: {avg_1:.2f}%")
    
    # 2. Pullback
    df_2 = df.dropna(subset=['pullback_roi'])
    fill_rate_2 = len(df_2) / len(df) * 100
    win_2 = (df_2['pullback_roi'] > 0).mean() * 100
    avg_2 = df_2['pullback_roi'].mean() * 100
    print(f"[TACTIC 2: Pullback] Win Rate: {win_2:.1f}% | Avg ROI: {avg_2:.2f}% | Fill Rate: {fill_rate_2:.1f}%")
    
    # 3. Breakout
    df_3 = df.dropna(subset=['breakout_roi'])
    fill_rate_3 = len(df_3) / len(df) * 100
    win_3 = (df_3['breakout_roi'] > 0).mean() * 100
    avg_3 = df_3['breakout_roi'].mean() * 100
    print(f"[TACTIC 3: Breakout] Win Rate: {win_3:.1f}% | Avg ROI: {avg_3:.2f}% | Fill Rate: {fill_rate_3:.1f}%")
    
    # Winner Check
    best_tactic = "None"
    best_roi = -999
    
    if avg_1 > best_roi: 
        best_tactic = "Instant (Ride the Tail)"
        best_roi = avg_1
    if avg_2 > best_roi:
        best_tactic = "Pullback (Bite the Belly)"
        best_roi = avg_2
    if avg_3 > best_roi:
        best_tactic = "Breakout (Hunt the Head)"
        best_roi = avg_3
        
    summary = f"""
🏆 CHAMPION TACTIC: {best_tactic}
[TACTIC 1: Instant] Win Rate: {win_1:.1f}% | Avg ROI: {avg_1:.2f}%
[TACTIC 2: Pullback] Win Rate: {win_2:.1f}% | Avg ROI: {avg_2:.2f}% | Fill Rate: {fill_rate_2:.1f}%
[TACTIC 3: Breakout] Win Rate: {win_3:.1f}% | Avg ROI: {avg_3:.2f}% | Fill Rate: {fill_rate_3:.1f}%
Insight: Whale movements are often followed by...
"""
    if best_tactic == "Instant": summary += "...Continuation (Momentum is King)."
    elif best_tactic == "Pullback": summary += "...Regression (Buy the Dip)."
    elif best_tactic == "Breakout": summary += "...Second Wind (Confirmation is Key)."
    
    print(summary)
    with open("whale_result.txt", "w", encoding='utf-8') as f:
        f.write(summary)

if __name__ == "__main__":
    analyze_whale_surfing()
