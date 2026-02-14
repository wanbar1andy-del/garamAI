
import pandas as pd
import glob
import os
import backtrader as bt
from datetime import datetime

# Define Strategy
class IntradayHeroStrategy(bt.Strategy):
    params = (
        ('warmup', 30),
        ('breakout_th', 0.02), # 2% return
        ('vol_mult', 3.0),
        ('trail_stop', 0.01),
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            # Simple Indicators (Intraday)
            self.inds[d] = {
                'vol_ma': bt.indicators.SMA(d.volume, period=20),
                'high_roll': bt.indicators.Highest(d.high, period=30),
            }
        self.equity_log = []

    def next(self):
        # Log Equity
        self.equity_log.append({
            'ts': self.datas[0].datetime.datetime(0),
            'Total_Equity': self.broker.getvalue()
        })

        for d in self.datas:
            if len(d) < self.params.warmup: continue
            
            pos = self.getposition(d).size
            
            # Entry Logic
            if pos == 0:
                # 1. Price Momentum: Close > Open + 2% (Intraday strength)
                # Ideally, compare to Today's Open. Since it's day1 data, d.open[0] is current bar open.
                # We need Today's Open.
                # Approx: Close > Period High (Breakout)
                
                # Check Volume Spike
                vol_cond = d.volume[0] > self.inds[d]['vol_ma'][0] * self.params.vol_mult
                
                # Check Breakout (Price is at 30m High)
                price_cond = d.close[0] >= self.inds[d]['high_roll'][0]
                
                if vol_cond and price_cond:
                    # Buy Sizing (10% of equity)
                    cash = self.broker.getcash()
                    size = int((cash * 0.1) / d.close[0])
                    if size > 0:
                        self.buy(data=d, size=size)
                        print(f"[{d.datetime.datetime(0)}] BUY {d._name} @ {d.close[0]}")

            # Exit Logic (Trailing Stop)
            elif pos > 0:
                # Simple Trailing: If price drops 1% from Entry High? 
                # Or just Close < High - 1%
                # Backtrader TrailingStop is order based. Let's do manual.
                # If Close < AvgPrice * (1 - stop)
                
                entry_price = self.getposition(d).price
                if d.close[0] < entry_price * (1 - self.params.trail_stop):
                    self.close(data=d)
                    print(f"[{d.datetime.datetime(0)}] SELL {d._name} @ {d.close[0]} (Stop)")
                elif d.close[0] > entry_price * 1.05: # Take Profit 5%
                    self.close(data=d)
                    print(f"[{d.datetime.datetime(0)}] SELL {d._name} @ {d.close[0]} (TP)")

def run_replay():
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10000000) # 10M KRW
    cerebro.broker.setcommission(commission=0.0023) # 0.23%
    
    # Load Data
    data_dir = "GARAM_Data/day1_replay"
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    # Filter only top candidates? Or all?
    # Loading 400 is heavy for Cerebro. Let's load extracted summary top 10.
    
    summary_path = os.path.join(data_dir, "extraction_summary.csv")
    if os.path.exists(summary_path):
        sum_df = pd.read_csv(summary_path)
        # Filter > 30 bars
        sum_df = sum_df[sum_df['bars'] > 30]
        top_symbols = sum_df.head(20)['symbol'].astype(str).tolist()
        # Ensure 6 digits
        top_symbols = [s.zfill(6) for s in top_symbols]
    else:
        top_symbols = []

    print(f"Loading Top {len(top_symbols)} symbols (Bars > 30) for Replay...")
    
    cnt = 0
    for f in files:
        sym = os.path.basename(f).replace(".csv", "")
        if top_symbols and sym not in top_symbols: continue

        data = bt.feeds.GenericCSVData(
            dataname=f,
            dtformat='%Y-%m-%d %H:%M:%S',
            datetime=0,
            open=1, high=2, low=3, close=4, volume=5,
            openinterest=-1,
            timeframe=bt.TimeFrame.Minutes
        )
        cerebro.adddata(data, name=sym)
        cnt += 1
        
    print(f"Loaded {cnt} feeds.")
    
    cerebro.addstrategy(IntradayHeroStrategy)
    
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())
    results = cerebro.run()
    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
    
    # Extract Equity Curve
    strat = results[0]
    # We didn't enable observers or analyzers.
    # To get equity curve, we need an analyzer or check cache?
    # Simpler: Add Writer
    
    # Or just rerun with a custom observer?
    # Let's add a simple text logger in next() to a list
    
    if hasattr(strat, 'equity_log'):
        df = pd.DataFrame(strat.equity_log)
        df.to_csv("GARAM_Data/day1_equity_diversified.csv", index=False)
        print("Saved Profit Curve Data.")
    
if __name__ == "__main__":
    run_replay()
