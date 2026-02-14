
import pandas as pd
import glob
import os
import backtrader as bt
import datetime
import itertools

# Strategy Definition (Parametrized)
class IntradayHeroStrategy(bt.Strategy):
    params = (
        ('warmup', 30),
        ('vol_mult', 3.0),      # To be optimized
        ('trail_stop', 0.01),   # To be optimized
        ('high_period', 30),    # To be optimized
        ('tp', 0.05),           # To be optimized
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                'vol_ma': bt.indicators.SMA(d.volume, period=20),
                'high_roll': bt.indicators.Highest(d.high, period=self.params.high_period),
            }

    def next(self):
        for d in self.datas:
            if len(d) < self.params.warmup: continue
            
            pos = self.getposition(d).size
            
            # Entry Logic
            if pos == 0:
                if d.datetime.time(0) >= datetime.time(14, 30): continue

                vol_cond = d.volume[0] > self.inds[d]['vol_ma'][0] * self.params.vol_mult
                price_cond = d.close[0] >= self.inds[d]['high_roll'][0]
                
                if vol_cond and price_cond:
                    cash = self.broker.getcash()
                    size = int((cash * 0.1) / d.close[0])
                    if size > 0:
                        self.buy(data=d, size=size)

            # Exit Logic
            elif pos > 0:
                if d.datetime.time(0) >= datetime.time(15, 0):
                    self.close(data=d)
                    return

                entry_price = self.getposition(d).price
                if d.close[0] < entry_price * (1 - self.params.trail_stop):
                    self.close(data=d)
                elif d.close[0] > entry_price * (1 + self.params.tp): # Use Variable TP
                    self.close(data=d)

# Simulation Engine (5-Day Loop)
def run_simulation(vol_mult, trail_stop, take_profit):
    dates = ['2025-12-09', '2025-12-10', '2025-12-11', '2025-12-12', '2026-01-02']
    current_cash = 10000000.0
    
    if 'DATA_CACHE' not in globals():
        global DATA_CACHE
        DATA_CACHE = {}
        data_dir = "GARAM_Data/5day_replay"
        files = glob.glob(os.path.join(data_dir, "*.csv"))
        for f in files:
            sym = os.path.basename(f).replace(".csv", "")
            try:
                df = pd.read_csv(f)
                df['ts'] = pd.to_datetime(df['ts'])
                DATA_CACHE[sym] = df
            except: pass
            
    for date_str in dates:
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(current_cash)
        cerebro.broker.setcommission(commission=0.0023)
        
        target_date = pd.to_datetime(date_str).date()
        
        feeds_added = 0
        for sym, df in DATA_CACHE.items():
            day_df = df[df['ts'].dt.date == target_date]
            if len(day_df) < 30: continue
            
            data = bt.feeds.PandasData(
                dataname=day_df.set_index('ts'),
                open='open', high='high', low='low', close='close', volume='volume',
                openinterest=None,
                timeframe=bt.TimeFrame.Minutes
            )
            cerebro.adddata(data, name=sym)
            feeds_added += 1
            
        if feeds_added == 0: continue
            
        cerebro.addstrategy(IntradayHeroStrategy, vol_mult=vol_mult, trail_stop=trail_stop, tp=take_profit)
        cerebro.run()
        current_cash = cerebro.broker.getvalue()
        
    return current_cash

def optimize():
    # Phase 2: Optimize TP
    vol = 2.0
    stop = 0.01
    
    tp_range = [0.05, 0.10, 0.15, 0.20, 0.25, 0.99]
    
    results = []
    print(f"Starting TP Optimization (Vol={vol}, Stop={stop})...")
    
    for tp in tp_range:
        print(f"Testing TP={tp}...")
        final_eq = run_simulation(vol, stop, tp)
        pnl = (final_eq - 10000000.0) / 10000000.0 * 100.0
        print(f"  -> Result: {pnl:.2f}%")
        results.append({'tp': tp, 'pnl': pnl})
        
    results.sort(key=lambda x: x['pnl'], reverse=True)
    
    print("\n=== Top Configurations ===")
    for r in results:
        print(f"TP: {r['tp']}, PnL: {r['pnl']:.2f}%")

if __name__ == "__main__":
    optimize()
