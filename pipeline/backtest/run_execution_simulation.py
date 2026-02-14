import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add path to import AlphaGenius_V2
sys.path.append(str(Path(__file__).parent))
from run_alpha_robust import AlphaGenius_V2, load_data

def calculate_market_impact(order_value, price, minute_volume, volatility):
    """
    Simulates Market Impact (Slippage) using Square Root Law.
    Impact ~ Volatility * sqrt(OrderSize / Volume)
    """
    if minute_volume * price == 0: return 0.05 # Max penalty for illiquid
    
    participation_rate = order_value / (minute_volume * price)
    
    # Impact Model coefficient (0.5 is standard for liquid markets, 1.0 for tighter)
    c = 0.5 
    
    # Estimated Price movement due to our order
    impact_bps = c * volatility * np.sqrt(participation_rate)
    
    # Cap impact reasonably (e.g. max 5%)
    return min(impact_bps, 0.05)

def run_execution_test():
    print("::: GARAM REAL-WORLD ALIGNMENT TEST (100M KRW) :::")
    print("Testing: Naive Entry vs VBP (Volume Based Placement)")
    
    # 1. Setup Environment
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    alpha = AlphaGenius_V2()
    
    closes, volumes = load_data(data_dir, "universe.csv", "20250601", "20251212")
    print(f"[Exec] Data Loaded: {closes.shape}")
    
    # 2. Generate Signals
    signals = alpha.calculate_signals(closes, volumes)
    
    # 3. Execution Simulation
    TARGET_ORDER_SIZE = 100_000_000 # 100 Million KRW
    
    results = []
    
    print("\n[Exec] Simulating Orders...")
    
    # Iterate through signals
    # Use valid signals (Score > 0)
    # We focus on "Hero" signals (Score >= 7.0) for this test
    hero_signals = signals[signals >= 7.0].stack()
    
    # Limit to 50 samples for speed
    if len(hero_signals) > 50:
        hero_signals = hero_signals.sample(50, random_state=42)
        
    for (ts, sym), score in hero_signals.items():
        if sym not in closes.columns: continue
        
        # Get market data window around signal
        try:
            loc = closes.index.get_loc(ts)
        except KeyError: continue
        
        # 5-minute window for VBP
        window_c = closes[sym].iloc[loc:loc+5] 
        window_v = volumes[sym].iloc[loc:loc+5]
        
        if len(window_c) < 5: continue
        
        entry_price = window_c.iloc[0]
        if entry_price <= 0: continue
        
        # --- Scenario A: Naive (Instant 100M) ---
        # Volatility estimated from recent 20 bars
        recent_c = closes[sym].iloc[loc-20:loc]
        volatility = recent_c.pct_change().std()
        if np.isnan(volatility): volatility = 0.005 # Default 0.5%
        
        vol_1m = window_v.iloc[0]
        impact_a = calculate_market_impact(TARGET_ORDER_SIZE, entry_price, vol_1m, volatility)
        
        exec_price_a = entry_price * (1 + impact_a)
        gap_a = (exec_price_a - entry_price) / entry_price
        
        # --- Scenario B: VBP (Split into 5 mins) ---
        # 20M per minute
        chunk_size = TARGET_ORDER_SIZE / 5
        total_shares = 0
        total_cost = 0
        
        params_impacts = []
        
        for i in range(5):
            p = window_c.iloc[i]
            v = window_v.iloc[i]
            
            # Impact for smaller chunk
            imp = calculate_market_impact(chunk_size, p, v, volatility)
            params_impacts.append(imp)
            
            exec_p = p * (1 + imp)
            shares = chunk_size / exec_p
            
            total_shares += shares
            total_cost += chunk_size
            
        avg_exec_price_b = total_cost / total_shares
        gap_b = (avg_exec_price_b - entry_price) / entry_price # Compare to initial signal price
        
        # --- Anonymity Score ---
        # Based on Max Participation Rate in VBP
        # If we take > 10% of volume, Anonymity drops
        max_part = 0
        for i in range(5):
             v = window_v.iloc[i]
             p = window_c.iloc[i]
             if v*p > 0:
                 max_part = max(max_part, chunk_size / (v*p))
        
        # Score: 100 - (Participation% * 500)
        # e.g. 1% part -> 100 - 5 = 95
        # e.g. 10% part -> 100 - 50 = 50
        anonymity_score = max(0, 100 - (max_part * 500))
        
        results.append({
            "ts": ts,
            "sym": sym,
            "score": score,
            "volatility": volatility,
            "naive_slippage_bps": gap_a * 10000,
            "vbp_slippage_bps": gap_b * 10000,
            "improvement_bps": (gap_a - gap_b) * 10000,
            "anonymity": anonymity_score
        })

    # Summary
    df_res = pd.DataFrame(results)
    print("\n" + "="*60)
    print(f"📊 EXECUTION TEST RESULTS (Samples: {len(df_res)})")
    print("="*60)
    print(f"Avg Naive Slippage: {df_res['naive_slippage_bps'].mean():.2f} bps")
    print(f"Avg VBP Slippage  : {df_res['vbp_slippage_bps'].mean():.2f} bps")
    print(f"Avg Improvement   : {df_res['improvement_bps'].mean():.2f} bps")
    print(f"Avg Anonymity     : {df_res['anonymity'].mean():.1f} / 100")
    
    print("\n[VBP Efficiency Analysis]")
    success_rate = (df_res['improvement_bps'] > 0).mean() * 100
    print(f"VBP Win Rate: {success_rate:.1f}% (Cases where VBP beat Naive)")
    
    # Check Target
    if df_res['anonymity'].mean() >= 95:
        print("✅ ANONYMITY TARGET (95) ACHIEVED")
    else:
        print(f"⚠️ ANONYMITY TARGET MISSED ({df_res['anonymity'].mean():.1f})")
        print("   -> Needs smaller chunks or more liquid targets.")

if __name__ == "__main__":
    run_execution_test()
