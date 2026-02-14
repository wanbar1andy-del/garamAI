
import pandas as pd
import glob
import os
import backtrader as bt
import datetime

# Define Strategy
class ConcentrationStrategy(bt.Strategy):
    params = (
        ('warmup', 30),
        ('max_slots', 5),
        ('concentration_target', 0.6), # 3 slots / 5 = 60%
        ('normal_target', 0.2),       # 1 slot / 5 = 20%
        ('strong_threshold', 0.05),   # 5% return to trigger concentration
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                'return': (d.close - d.open) / d.open, # Intraday Return (approx)
            }
        self.allocation_log = []

    def next(self):
        # 1. Warmup
        if len(self.datas[0]) < self.params.warmup: return
        
        # 2. Rank Candidates by Intraday Return
        candidates = []
        for d in self.datas:
            # Check data validity
            if len(d) < 1: continue
            
            # Simple Breakout Logic for Eligibility
            # (Reuse previous logic: Vol Spike?)
            # For this test, assume all loaded symbols are "Candidates" if Price > Open
            
            # Intraday Cumulative Return (Strength)
            # Since data starts at 09:00, use d.close[0] vs d.open[-len(d)+1] approximation?
            # Better: Store open price in __init__
            # But Backtrader datas are lines.
            # Simple way: (d.close[0] - d.open[-len(d)+1]) if len > 0
            # Note: len(d) grows.
            # d.open array access: d.open.array[0] is the first bar.
            
            initial_open = d.open.array[0]
            cum_ret = (d.close[0] - initial_open) / initial_open
            
            candidates.append((d, cum_ret))
        
        # Sort by Cumulative Return
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 3. Determine Identification (Top 1)
        target_allocation = {}
        
        if candidates:
            top_d, top_ret = candidates[0]
            
            if top_ret > self.params.strong_threshold:
                # Strong Hero found! (e.g. > 5% Day Return)
                # Allocate 3 Slots (60%)
                target_allocation[top_d] = self.params.concentration_target
                
                # Fill remaining 2 slots with next candidates
                remaining_slots = self.params.max_slots - 3 # 2 slots left
                
                for i in range(1, min(1 + remaining_slots, len(candidates))):
                    d, _ = candidates[i]
                    target_allocation[d] = self.params.normal_target
                    
            else:
                # Normal mode: Equal weight 5 slots
                for i in range(min(self.params.max_slots, len(candidates))):
                    d, _ = candidates[i]
                    target_allocation[d] = self.params.normal_target

        # 4. Execute Rebalance
        # Note: Backtrader's order_target_percent is useful here
        
        # First, close/reduce positions not in target or target reduced
        # Then open/increase positions
        
        # Log Allocation
        log_entry = {'ts': self.datas[0].datetime.datetime(0)}
        log_entry['Total_Equity'] = self.broker.getvalue()
        
        for d in self.datas:
            target = target_allocation.get(d, 0.0)
            self.order_target_percent(d, target=target)
            
            name = d._name
            log_entry[name] = self.broker.getposition(d).size * d.close[0] # Equity Value
            
        self.allocation_log.append(log_entry)

def run_concentration_sim():
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10000000)
    cerebro.broker.setcommission(commission=0.0023)
    
    # Load Data (Top 10)
    data_dir = "GARAM_Data/day1_replay"
    summary_path = os.path.join(data_dir, "extraction_summary.csv")
    
    if os.path.exists(summary_path):
        sum_df = pd.read_csv(summary_path)
        sum_df = sum_df[sum_df['bars'] > 30] # Filter
        top_symbols = sum_df.head(10)['symbol'].astype(str).tolist()
        top_symbols = [s.zfill(6) for s in top_symbols]
    else:
        top_symbols = []

    print(f"Loading Top {len(top_symbols)} symbols...")
    
    for s in top_symbols:
        path = os.path.join(data_dir, f"{s}.csv")
        data = bt.feeds.GenericCSVData(
            dataname=path,
            dtformat='%Y-%m-%d %H:%M:%S',
            datetime=0,
            open=1, high=2, low=3, close=4, volume=5,
            openinterest=-1,
            timeframe=bt.TimeFrame.Minutes
        )
        cerebro.adddata(data, name=s)
        
    strategy = cerebro.addstrategy(ConcentrationStrategy)
    
    print("Running Concentration Simulation...")
    results = cerebro.run()
    strat = results[0]
    
    # Save Log
    log_df = pd.DataFrame(strat.allocation_log)
    if not log_df.empty:
        log_df.set_index('ts', inplace=True)
        # Normalize to % of Capital (approx) to show "3 slots"
        # Actually value is straight equity.
        log_df.to_csv("GARAM_Data/day1_allocation.csv")
        print("Allocation Log Saved: GARAM_Data/day1_allocation.csv")
    else:
        print("No log generated.")

if __name__ == "__main__":
    run_concentration_sim()
