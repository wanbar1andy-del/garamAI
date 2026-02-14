
import sys
import pandas as pd
import numpy as np
import random
import time
from pathlib import Path
from datetime import datetime, timedelta
import itertools
from concurrent.futures import ThreadPoolExecutor

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Imports
from core.engine.typhoon_orchestrator import TyphoonOrchestrator
from core.active_config.tactical_genome import dna
try:
    from scripts.neural_brain import GaramNeuralBrain
    import torch
except ImportError:
    pass

class ParamSearchBot(TyphoonOrchestrator):
    def __init__(self, params):
        super().__init__()
        self.params_override = params # {threshold, stop_pct, guard ...}
        self.capital = 100_000_000
        self.position = 0
        self.current_equity = self.capital
        
        # Override DNA for this instance virtually
        # In real engine we use dna.get(), here we mock logic
        self.oss_threshold = params['oss_threshold']
        self.stop_pct = params['stop_pct']
        
    def _process_tick(self, tick):
        self.current_price = tick['price']
        
        if self.phase == "PHASE_0_IDLE":
            score = tick.get('oss_score', 0)
            if score > self.oss_threshold and self.position == 0:
                self.phase = "PHASE_1_DISCOVERY"
                self._transition_to_trigger()

        elif self.phase == "PHASE_2_TRIGGER":
            if self.current_price > self.entry_price * 1.01:
                self.phase = "PHASE_3_FORMATION"
            elif self.current_price < self.entry_price * 0.99:
                self.execute_sell("CUT", self.current_price)
                self.phase = "PHASE_0_IDLE"

        elif self.phase == "PHASE_3_FORMATION":
            self.highest_price = max(self.highest_price, self.current_price)
            stop_price = self.highest_price * (1 - self.stop_pct)
            if self.current_price < stop_price:
                self.phase = "PHASE_4_EXTRACTION"
                
        elif self.phase == "PHASE_4_EXTRACTION":
            self.execute_sell("PROFIT", self.current_price)
            self.phase = "PHASE_0_IDLE"
            
    def _transition_to_trigger(self):
        self.phase = "PHASE_2_TRIGGER"
        self.entry_price = self.current_price
        self.highest_price = self.current_price
        self.execute_buy(self.current_price)

    def execute_buy(self, price):
        cost_price = price * 1.0005
        max_qty = int(self.capital / cost_price)
        if max_qty > 0:
            self.capital -= max_qty * cost_price
            self.position = max_qty
            self.avg_price = cost_price

    def execute_sell(self, reason, price):
        if self.position == 0: return
        sell_price = price * 0.9995
        revenue = self.position * sell_price
        # Tax/Fee 0.23%
        net_revenue = revenue * 0.9977 
        self.capital += net_revenue
        self.current_equity = self.capital
        self.position = 0

def load_data_long_term(symbol="005930"):
    path = PROJECT_ROOT / f"GARAM_Data/history/minute/{symbol}.csv"
    if not path.exists(): return pd.DataFrame() 
    
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    
    if 'date' in df.columns:
        df['time'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
    else:
        df['time'] = df.index
        
    df = df.dropna(subset=['time'])
    
    # June 2025 to Feb 2026
    mask = (df['time'] >= "2025-06-01") & (df['time'] <= "2026-02-06")
    df = df.loc[mask].sort_values('time').reset_index(drop=True)
    
    # Inject Signal Logic (Same as before)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    cond = (df['ma5'] > df['ma20'])
    df['oss_score'] = 0.0
    df.loc[cond, 'oss_score'] = 7.0 
    
    cond_strong = (df['ma5'] > df['ma20']) & (df['ma20'] > df['ma60'])
    df.loc[cond_strong, 'oss_score'] = 8.5 
    
    cond_weak = (df['ma5'] > df['ma20']) & (df['ma20'] < df['ma60'])
    df.loc[cond_weak, 'oss_score'] = 7.5 

    return df

def run_grid_search():
    print("=== [GOLDEN RATIO SEARCH] Parameter Grid Search (Jun 2025 - Feb 2026) ===")
    
    df = load_data_long_term()
    if df.empty:
        print("No Data found.")
        return

    # Parameter Space (Refined around 7.2 / 6%)
    thresholds = [7.0, 7.2, 7.4, 7.5, 8.0]
    stops = [0.04, 0.05, 0.06, 0.07, 0.08]
    
    combinations = list(itertools.product(thresholds, stops))
    best_ret = -999.0
    best_combo = None
    results = []
    
    start_time = time.time()
    last_report_time = start_time
    
    total_tasks = len(combinations)
    
    print(f"[SEARCH] Testing {total_tasks} combinations...")
    
    for i, (th, st) in enumerate(combinations):
        
        # Periodic Report (Simulated 5s for demo, user asked 5 min but task is fast)
        # We report progress.
        curr_time = time.time()
        if curr_time - last_report_time > 30: # Report every 30s logic
            elapsed = (curr_time - start_time) / 60
            print(f"   >> Progress: {i}/{total_tasks} ({i/total_tasks*100:.1f}%) - Best so far: {best_ret:.2f}%")
            last_report_time = curr_time
            
        params = {'oss_threshold': th, 'stop_pct': st}
        bot = ParamSearchBot(params)
        
        # Run Sim
        for row in df.itertuples():
            tick = {'price': row.close, 'oss_score': row.oss_score, 'time': row.time}
            bot._process_tick(tick)
            
        final_ret = ((bot.current_equity / 100_000_000) - 1) * 100
        results.append((th, st, final_ret))
        
        if final_ret > best_ret:
            best_ret = final_ret
            best_combo = (th, st)
            
    # Final Report
    print("\n" + "="*50)
    print(" [GOLDEN RATIO DISCOVERED]")
    print("="*50)
    print(f"Best Return     : {best_ret:+.2f}% (Dec 2025)")
    print(f"Optimal Threshold: {best_combo[0]}")
    print(f"Optimal Stop    : {best_combo[1]*100}%")
    
    print("\n[Top 5 Configurations]")
    results.sort(key=lambda x: x[2], reverse=True)
    for r in results[:5]:
        print(f"   * Score {r[0]} / Stop {r[1]*100:.0f}% -> {r[2]:+.2f}%")
        
    print("-" * 50)
    
    # Heatmap Data Save
    save_path = PROJECT_ROOT / "reports/golden_ratio_search.csv"
    pd.DataFrame(results, columns=['Threshold', 'Stop_Pct', 'Return']).to_csv(save_path, index=False)
    print(f"[DATA] Saved grid search data to {save_path}")

if __name__ == "__main__":
    run_grid_search()
