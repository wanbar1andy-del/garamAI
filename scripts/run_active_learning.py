
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import itertools
from tqdm import tqdm

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

class ActiveLearnerBot:
    def __init__(self):
        self.capital = 100_000_000
        self.position = 0
        self.equity_curve = []
        self.param_log = []
        
        # Candidate Scenarios to test "every moment" (Periodically)
        self.threshold_candidates = [7.0, 7.5, 8.0, 8.5]
        self.stop_candidates = [0.03, 0.05, 0.07, 0.10]
        self.combinations = list(itertools.product(self.threshold_candidates, self.stop_candidates))
        
        # Current active parameters
        self.curr_th = 8.0
        self.curr_stop = 0.05
        
        # Optimization settings
        self.lookback_window = 60 * 24 * 3  # Look back 3 days (approx 1200 bars) to find what's working
        self.reopt_interval = 60            # Re-evaluate every hour

    def fast_optimize(self, recent_df):
        """
        [ACTIVE LEARNING KERNEL]
        Simulate ALL scenarios on recent history to find the winner.
        """
        best_perf = -9999
        best_combo = (8.0, 0.05) # Default
        
        # Vectorized-ish simulation for speed
        # We process close prices and scores
        closes = recent_df['close'].values
        scores = recent_df['oss_score'].values
        
        for th, stop in self.combinations:
            # Quick Sim
            sim_cap = 100_000_000
            sim_pos = 0
            sim_entry = 0
            sim_high = 0
            
            # Simple loop is faster than pandas iter
            for i in range(len(closes)):
                price = closes[i]
                score = scores[i]
                
                if sim_pos == 0:
                    if score > th:
                        sim_pos = int(sim_cap / (price * 1.0005))
                        sim_cap -= sim_pos * (price * 1.0005)
                        sim_entry = price
                        sim_high = price
                elif sim_pos > 0:
                    sim_high = max(sim_high, price)
                    if price < sim_high * (1 - stop):
                        sim_cap += sim_pos * (price * 0.9995) * 0.9977
                        sim_pos = 0
            
            # Finalize
            final_val = sim_cap
            if sim_pos > 0: final_val += sim_pos * closes[-1]
            
            if final_val > best_perf:
                best_perf = final_val
                best_combo = (th, stop)
                
        return best_combo

    def run(self, df):
        print("\n=== [ACTIVE LEARNING] Dynamic Scenario Testing ===")
        print(f"Data: {len(df)} bars | Candidates: {len(self.combinations)} scenarios")
        print("Strategy: Re-test 3-day history every hour to pick the 'Hot Hand'.")
        
        entry_price = 0
        highest_price = 0
        
        # Progress bar
        pbar = tqdm(total=len(df))
        
        for i, row in enumerate(df.itertuples()):
            # 1. Active Learning (Re-optimization)
            if i > self.lookback_window and i % self.reopt_interval == 0:
                # Slice recent history
                recent_hist = df.iloc[i-self.lookback_window : i]
                # Find best params derived from recent past
                best_th, best_stop = self.fast_optimize(recent_hist)
                
                # ADAPT!
                self.curr_th = best_th
                self.curr_stop = best_stop
                self.param_log.append({'time': row.time, 'th': best_th, 'stop': best_stop})
            
            # 2. Execution (Using the Learned Param)
            price = row.close
            score = row.oss_score
            
            if self.position == 0:
                if score > self.curr_th:
                    self.position = int(self.capital / (price * 1.0005))
                    self.capital -= self.position * (price * 1.0005)
                    entry_price = price
                    highest_price = price
                    
            elif self.position > 0:
                highest_price = max(highest_price, price)
                stop_price = highest_price * (1 - self.curr_stop) # Dynamic Stop
                
                if price < stop_price:
                    self.capital += self.position * (price * 0.9995) * 0.9977
                    self.position = 0
            
            # Update Equity
            eq = self.capital
            if self.position > 0: eq += self.position * price - (self.position * entry_price)
            self.equity_curve.append(eq)
            
            pbar.update(1)
            
        pbar.close()
        
        # Report
        final_eq = self.equity_curve[-1]
        ret = ((final_eq / 100_000_000) - 1) * 100
        
        print("\n" + "="*50)
        print(" [ACTIVE LEARNING RESULT]")
        print("="*50)
        print(f"Final Equity : {final_eq:,.0f} KRW")
        print(f"Total Return : {ret:+.2f}%")
        
        # Analyze Params
        ths = [x['th'] for x in self.param_log]
        print("\n[Behavior Analysis]")
        print(f"Adapts Threshold between: {min(ths)} ~ {max(ths)}")
        
        # Plot
        plt.figure(figsize=(10,6))
        plt.plot(self.equity_curve, label='Equity')
        plt.title('Active Learning Performance')
        plt.savefig(PROJECT_ROOT / "reports/active_learning_result.png")
        print("[GRAPH] Saved report.")

def load_data():
    symbol = "005930"
    path = PROJECT_ROOT / f"GARAM_Data/history/minute/{symbol}.csv"
    if not path.exists(): return pd.DataFrame() 
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    if 'date' in df.columns: df['time'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
    else: df['time'] = df.index
    df = df.dropna(subset=['time'])
    mask = (df['time'] >= "2025-06-01") & (df['time'] <= "2026-02-06")
    df = df.loc[mask].sort_values('time').reset_index(drop=True)
    
    # Simple Signals
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # Multi-level scoring for scenarios to pick from
    df['oss_score'] = 0.0
    
    # We assign a loose score, so the Threshold filter can enable/disable it
    # If ma5 > ma20, we give basic 7.0
    # If ma20 > ma60, we boost to 8.0
    # If vol is high, maybe boost? (Simplified for now)
    
    cond_basic = (df['ma5'] > df['ma20'])
    df.loc[cond_basic, 'oss_score'] = 7.2
    
    cond_strong = (df['ma5'] > df['ma20']) & (df['ma20'] > df['ma60'])
    df.loc[cond_strong, 'oss_score'] = 8.2
    
    return df

if __name__ == "__main__":
    df = load_data()
    if not df.empty:
        bot = ActiveLearnerBot()
        bot.run(df)
