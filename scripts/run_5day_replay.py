
import pandas as pd
import glob
import os
import backtrader as bt
import datetime

# Reuse Intraday Strategy
class IntradayHeroStrategy(bt.Strategy):
    params = (
        ('warmup', 30),
        ('breakout_th', 0.02),
        ('vol_mult', 3.0),
        ('trail_stop', 0.01),
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
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
                # EOD Check (Don't enter after 14:30)
                if d.datetime.time(0) >= datetime.time(14, 30): continue

                vol_cond = d.volume[0] > self.inds[d]['vol_ma'][0] * self.params.vol_mult
                price_cond = d.close[0] >= self.inds[d]['high_roll'][0]
                
                if vol_cond and price_cond:
                    # Sizing: 10%
                    cash = self.broker.getcash()
                    size = int((cash * 0.1) / d.close[0])
                    if size > 0:
                        self.buy(data=d, size=size)

            # Exit Logic
            elif pos > 0:
                # EOD Force Sell (15:00)
                if d.datetime.time(0) >= datetime.time(15, 0):
                    self.close(data=d)
                    return

                entry_price = self.getposition(d).price
                if d.close[0] < entry_price * (1 - self.params.trail_stop):
                    self.close(data=d)
                elif d.close[0] > entry_price * 1.05: # TP 5%
                    self.close(data=d)

def run_5day_replay():
    # 5 Independent Sessions to avoid Data Gap issues
    dates = ['2025-12-09', '2025-12-10', '2025-12-11', '2025-12-12', '2026-01-02']
    
    current_cash = 10000000.0
    equity_curve = []
    
    for date_str in dates:
        print(f"--- Simulating {date_str} (Start Cash: {current_cash:.0f}) ---")
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(current_cash)
        cerebro.broker.setcommission(commission=0.0023)
        
        # Load Data for this specific date ONLY
        data_dir = "GARAM_Data/5day_replay"
        files = glob.glob(os.path.join(data_dir, "*.csv"))
        
        feeds_loaded = 0
        for f in files:
            sym = os.path.basename(f).replace(".csv", "")
            try:
                # Pre-filter by date in pandas to ensure clean feed
                df = pd.read_csv(f)
                df['ts'] = pd.to_datetime(df['ts'])
                
                # Filter by YYYY-MM-DD
                target_date = pd.to_datetime(date_str).date()
                day_df = df[df['ts'].dt.date == target_date]
                
                if len(day_df) < 30: continue # Skip if no data for this day
                
                # Create temp file for this day? 
                # Or use headerless csv? 
                # Backtrader needs a file or dataframe.
                # Passing DataFrame directly!
                
                data = bt.feeds.PandasData(
                    dataname=day_df.set_index('ts'),
                    open='open', high='high', low='low', close='close', volume='volume',
                    openinterest=None,
                    timeframe=bt.TimeFrame.Minutes
                )
                cerebro.adddata(data, name=sym)
                feeds_loaded += 1
            except Exception as e:
                # print(e)
                continue
                
        if feeds_loaded == 0:
            print(f"No data for {date_str}. Skipping.")
            continue
            
        cerebro.addstrategy(IntradayHeroStrategy)
        
        results = cerebro.run()
        
        # Update Cash
        current_cash = cerebro.broker.getvalue()
        
        # Extract Equity for this day
        strat = results[0]
        for entry in strat.equity_log:
             # Adjust equity to be continuous? 
             # The strat.equity_log value is based on 'current_cash' set at start of loop.
             # So it is continuous!
             equity_curve.append(entry)
             
    print(f"Final 5-Day Equity: {current_cash:.0f}")
    
    # Save Combined Equity
    pd.DataFrame(equity_curve).to_csv("GARAM_Data/5day_equity.csv", index=False)
    print("Saved GARAM_Data/5day_equity.csv")

if __name__ == "__main__":
    run_5day_replay()
