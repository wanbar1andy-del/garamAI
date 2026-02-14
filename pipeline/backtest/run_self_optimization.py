import pandas as pd
import numpy as np
import sys
from pathlib import Path
from run_alpha_robust import AlphaGenius_V2, load_data

def run_self_optimization():
    print("::: GARAM SELF-OPTIMIZATION SIMULATION :::")
    print("Objective: Replay past trades & measure improvement via Dynamic Thresholding.")
    
    # 1. Load Data
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    closes, volumes = load_data(data_dir, "universe.csv", "20250601", "20251212")
    
    # 2. Reconstruct Market Temperature (Volatility Index)
    # Market Vol = Mean of 20-day std of all stocks
    returns = closes.pct_change()
    vol_20 = returns.rolling(window=20).std()
    market_vol = vol_20.mean(axis=1) 
    vol_avg_100 = market_vol.rolling(window=100).mean()
    
    # Temp = (Vol_Short / Vol_Long)
    # Using User's definition: Cold < 0.8, Warm 0.8~1.2, Hot > 1.2
    market_temp = (market_vol / (vol_avg_100 + 1e-9)).fillna(1.0)
    
    # 3. Generate Raw Signals (AlphaGenius V2)
    alpha = AlphaGenius_V2()
    # Note: calculate_signals returns FILTERED score based on new logic.
    # To test "What IF", we need RAW scores.
    # We will simulate raw scores here again (simplified) or trust current logic?
    # The user asks: "Analyze past LOSSES... and see if parameter adjustment helps."
    # So we need to find where effective trades happened.
    
    # Let's use the `calculate_signals` but assume it returns `neuro_score` (which IS dynamic now).
    # Wait, I just updated `calculate_signals` to USE dynamic threshold.
    # So the current `neuro_score` ALREADY reflects some dynamic logic.
    # But I need to compare "Static Score 5.0" vs "Dynamic Score".
    
    # I will manually calc Raw Score (Static 5.0) and Dynamic Score.
    print("[Self] Calculating Raw & Dynamic Scores...")
    
    # --- Simplified Signal Generation ---
    c_5m = closes.resample('5min', label='right').last().ffill()
    v_5m = volumes.resample('5min', label='right').sum().fillna(0)
    v_5m = v_5m.reindex(c_5m.index).fillna(0)
    
    c_daily = closes.resample('D').last().ffill()
    ma60 = c_daily.rolling(60).mean().shift(1).reindex(c_5m.index, method='ffill')
    above_struct = (c_5m > ma60)
    
    v_ma20 = v_5m.rolling(20).mean()
    vol_ratio = v_5m / (v_ma20 + 1e-9)
    huge_vol = (vol_ratio > 3.0)
    
    roll = c_5m.rolling(20)
    bw = (roll.mean() + 2*roll.std() - (roll.mean() - 2*roll.std())) / roll.mean()
    z = (bw - bw.rolling(100).mean()) / bw.rolling(100).std()
    tight = (z < -0.5)
    
    # Raw Score Components
    base = ((z < 0.5) & (vol_ratio > 1.5) & above_struct).astype(float) * 5.0
    boost_sq = tight.astype(float) * 2.0
    boost_vol = huge_vol.astype(float) * 2.0
    
    raw_score_5m = base + boost_sq + boost_vol
    raw_score = raw_score_5m.reindex(closes.index, method='ffill').fillna(0)
    
    # 4. Simulation Loop: Static vs Dynamic
    # Static: Entry if Score >= 7.0 (Fixed High Bar)
    # Dynamic: Entry if Score >= DynamicThreshold(Temp)
    
    # Dynamic Threshold Formula
    # Cold (<0.8): Low Threshold (5.0) - Hunt for sparks
    # Warm (0.8-1.2): Mid Threshold (7.0) - Standard
    # Hot (>1.2): High Threshold (9.0) - Anti-Fakeout
    
    temp_1m = market_temp.reindex(closes.index, method='ffill').fillna(1.0)
    
    results_static = []
    results_dynamic = []
    
    # Iterate signals
    # Find all potential entries (Score >= 5.0)
    candidates = raw_score[raw_score >= 5.0].stack()
    # Sample for speed (Top 500)
    if len(candidates) > 500:
        candidates = candidates.sample(500, random_state=42)
        
    print(f"\n[Self] Evaluating {len(candidates)} potential setups...")
    
    for (ts, sym), score in candidates.items():
        if sym not in closes.columns: continue
        
        # Market Temp at that time
        try:
            temp = temp_1m.loc[ts]
        except: continue
        
        # 1. Static Execution (Fixed 7.0)
        entry_static = (score >= 7.0)
        
        # 2. Dynamic Execution
        thresh_dyn = 7.0 # Default
        if temp < 0.8: thresh_dyn = 5.0 # Cold -> Lower bar
        elif temp > 1.2: thresh_dyn = 9.0 # Hot -> Higher bar
        
        entry_dynamic = (score >= thresh_dyn)
        
        # Measure Outcome (Next 60 min return)
        try:
            loc = closes.index.get_loc(ts)
            if loc + 60 >= len(closes): continue
            
            p_entry = closes[sym].iloc[loc]
            p_exit = closes[sym].iloc[loc+60]
            roi = (p_exit / p_entry) - 1.0
            
            # Log Static
            if entry_static:
                results_static.append(roi)
                
            # Log Dynamic
            if entry_dynamic:
                results_dynamic.append(roi)
                
        except: continue

    # 5. Comparative Report
    n_static = len(results_static)
    win_static = np.mean([r > 0 for r in results_static]) * 100 if n_static > 0 else 0
    avg_static = np.mean(results_static) * 100 if n_static > 0 else 0
    
    n_dynamic = len(results_dynamic)
    win_dynamic = np.mean([r > 0 for r in results_dynamic]) * 100 if n_dynamic > 0 else 0
    avg_dynamic = np.mean(results_dynamic) * 100 if n_dynamic > 0 else 0
    
    print("\n" + "="*50)
    print("📊 SELF-OPTIMIZATION REPORT")
    print("="*50)
    print(f"Condition | Trades | Win Rate | Avg ROI")
    print(f"----------|--------|----------|---------")
    print(f"STATIC    | {n_static:<6} | {win_static:5.1f}%  | {avg_static:5.2f}%")
    print(f"DYNAMIC   | {n_dynamic:<6} | {win_dynamic:5.1f}%  | {avg_dynamic:5.2f}%")
    print("-" * 50)
    
    improvement = avg_dynamic - avg_static
    print(f"\n[Validation] Profitability Improvement: {improvement:+.2f}%p")
    
    if improvement > 0:
        print("✅ SUCCESS: Dynamic Thresholding proved superior.")
        print("   -> Adopt this logic into Tactical DNA immediately.")
    else:
        print("⚠️ WARNING: Dynamic Logic needs tuning (No clear edge found).")
        
    # Analyze "Saved Losses" in Hot Market
    print("\n[Case Study: Hot Market Defense]")
    # Filter only Hot Market trades (>1.2)
    # How many STATIC losses were avoided by DYNAMIC?
    # Logic: If (Static Entry == True) AND (Dynamic Entry == False) AND (ROI < 0) -> Saved Loss
    
    saved_losses = 0
    for (ts, sym), score in candidates.items():
         try:
            temp = temp_1m.loc[ts]
            if temp <= 1.2: continue # Only check Hot market defense
            
            # Outcome
            loc = closes.index.get_loc(ts)
            p_entry = closes[sym].iloc[loc]
            p_exit = closes[sym].iloc[loc+60]
            roi = (p_exit / p_entry) - 1.0
            
            entry_s = (score >= 7.0)
            entry_d = (score >= 9.0) # Hot threshold
            
            if entry_s and not entry_d and roi < 0:
                saved_losses += 1
         except: pass

    print(f"🔥 Hot Market (Temp > 1.2):")
    print(f"   By raising threshold to 9.0, we avoided {saved_losses} false breakouts.")
    print("   (These were trades Static logic entered but Dynamic rejected, and they failed.)")

if __name__ == "__main__":
    run_self_optimization()
