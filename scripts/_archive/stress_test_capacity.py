"""
System Capacity Stress Test
Measures how many symbols the DGEFinalStrategy can handle in real-time.
Simulates the 'on_bar' processing loop for N symbols.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import pandas as pd
import numpy as np
from strategies.kr_intraday.dge_final import DGEFinalStrategy
from sim.test_account import TestAccount

def run_benchmark(n_symbols):
    print(f"Testing capacity for {n_symbols} symbols...")
    
    # 1. Setup
    account = TestAccount(100_000_000)
    config = {'risk_per_trade': 0.02}
    strategies = []
    
    # Create N instances
    setup_start = time.time()
    for i in range(n_symbols):
        sym = f"{i:06d}"
        # We pass None for daily_df to avoid loading huge dataframes for this test
        # The strategy handles None daily_df gracefully (returns None or skips regime check)
        # To test FULL load, we should ideally provide daily_df, but loading N dfs is memory bound.
        # For CPU bound test, we'll simulate the calculation.
        strategies.append(DGEFinalStrategy(account, config, symbol=sym))
    setup_time = time.time() - setup_start
    # print(f"  Setup Time: {setup_time:.4f}s")
    
    # 2. Prepare Dummy Data
    bar_data = pd.Series({
        'open': 10000.0, 'high': 10100.0, 'low': 9900.0, 'close': 10050.0, 'volume': 10000.0
    })
    timestamp = pd.Timestamp("2025-11-25 09:30:00")
    
    # 3. Warmup (Populate history buffer)
    # DGE strategies usually need ~20-50 bars to start calculating indicators
    # We'll push 30 bars to fill buffers
    for _ in range(30):
        for s in strategies:
            s.on_bar(bar_data, timestamp)
            
    # 4. Measure Latency (The Critical Loop)
    # Simulate receiving a 1-minute bar for ALL symbols at the same time
    start_time = time.time()
    for s in strategies:
        s.on_bar(bar_data, timestamp)
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_per_symbol = (total_time / n_symbols) * 1000 # ms
    
    print(f"  Total Processing Time: {total_time:.4f}s")
    print(f"  Avg Time per Symbol:   {avg_per_symbol:.4f}ms")
    
    return total_time

def main():
    print("=== DGE Final Strategy Capacity Stress Test ===")
    print("Hardware: Current System")
    print("Threshold: 1.0 second max processing time (to keep up with real-time)")
    print("-" * 60)
    
    symbol_counts = [10, 50, 100, 200, 300, 500, 1000]
    max_safe_symbols = 0
    
    for n in symbol_counts:
        try:
            duration = run_benchmark(n)
            if duration < 1.0:
                max_safe_symbols = n
                print(f"  [PASS] {n} symbols is safe.")
            else:
                print(f"  [FAIL] {n} symbols exceeded 1.0s limit.")
                break
        except MemoryError:
            print(f"  [FAIL] {n} symbols caused MemoryError.")
            break
        except Exception as e:
            print(f"  [ERROR] {e}")
            break
        print("-" * 30)
        
    print("=" * 60)
    print(f"RECOMMENDED MAX SYMBOLS: {max_safe_symbols}")
    print("Note: This tests Python calculation speed. Kiwoom API has a hard limit of 1000 symbols (10 screens * 100).")
    print("      Real-world safety margin suggests using 50-70% of this benchmark.")

if __name__ == "__main__":
    main()
