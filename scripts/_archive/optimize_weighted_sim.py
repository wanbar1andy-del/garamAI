import sys
import pandas as pd
import numpy as np
import itertools
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

sys.path.append("c:/garam/garam")
from scripts.run_weighted_sim import WeightedSimEngine

def evaluate(params):
    wa, wb, wc, wd = params
    # Turbo fixed at 1.0 for weight optimization
    eng = WeightedSimEngine(wa, wb, wc, wd, turbo_mult=1.0)
    
    # Run simulation (2 years approx)
    start = "2024-01-02"
    end = "2025-12-12" # Or today
    
    try:
        history = eng.run(start, end)
        if not history:
            return params, -99.0, 0.0
            
        initial = history[0]['equity']
        final = history[-1]['equity']
        ret = (final / initial) - 1.0
        return params, ret, final
    except Exception as e:
        return params, -99.0, 0.0

def main():
    print("=== Searching for Golden Ratio (Wa, Wb, Wc, Wd) ===")
    
    # 1. Define Search Space
    # Wa (Trend): 0.5 ~ 2.5
    # Wb (Revert): 0.0 ~ 2.0
    # Wc (Fear): -2.0 ~ 0.5 (Usually negative for safety, but maybe positive for aggressive?)
    # Wd (Hero): 0.0 ~ 3.0 (Quality)
    
    combinations = []
    
    # Strategy: Random Search (Efficient for high dimensional)
    for _ in range(50): # Increased to 50 for local search
        wa = round(random.uniform(1.0, 3.0), 1) # Center 2.0
        wb = round(random.uniform(0.5, 2.5), 1) # Center 1.5
        wc = round(random.uniform(1.5, 3.5), 1) # Center 2.7 (User wants Positive Vol?)
        wd = round(random.uniform(2.0, 4.0), 1) # Center 3.0
        combinations.append((wa, wb, wc, wd))
        
    print(f"Generated {len(combinations)} combinations...")
    
    # Pre-load data once (The engine class handles this via shared cache, 
    # but we instantiate one first to trigger the load)
    print("Loading Data into Cache...")
    dummy = WeightedSimEngine(1,0,0,0)
    dummy.load_data()
    print("Data Loaded.")
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(evaluate, c): c for c in combinations}
        
        for i, future in enumerate(as_completed(futures)):
            params, ret, final = future.result()
            results.append({
                'wa': params[0],
                'wb': params[1],
                'wc': params[2],
                'wd': params[3],
                'return': ret,
                'equity': final
            })
            if i % 1 == 0:
                print(f"Processed {i}/{len(combinations)}... Result: {ret*100:.1f}%")

    print(f"Optimization finished in {time.time() - start_time:.1f}s")
    
    # Sort by Return
    df = pd.DataFrame(results)
    df = df.sort_values(by='return', ascending=False)
    
    print("\n=== TOP 5 GOLDEN RATIOS ===")
    print(df.head(5).to_string(index=False))
    
    # Save
    df.to_csv("optimization_results_golden.csv", index=False)

if __name__ == "__main__":
    main()
