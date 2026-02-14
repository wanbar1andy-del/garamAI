
import pandas as pd
import backtrader as bt
import matplotlib.pyplot as plt
import os
import datetime

FILE_PATH = "GARAM_Data/5day_replay/424870.csv"
DATE_FILTER = "2025-12-11"
OUT_CHART = "results/reports/forensic_424870.png"

# Intraday Strategy with Logging
class ForensicStrategy(bt.Strategy):
    params = (
        ('vol_mult', 2.0),
        ('trail_stop', 0.05), # User requested "More Room" (5%)
        ('tp', 0.20)          # Let it run (20%)
    )

    def __init__(self):
        self.vol_ma = bt.indicators.SMA(self.data.volume, period=20)
        self.high_roll = bt.indicators.Highest(self.data.high, period=30)
        self.trades_log = []

    def next(self):
        # Entry Logic (Optimized)
        pos = self.position.size
        
        if pos == 0:
            if self.data.datetime.time() >= datetime.time(14, 30): return
            
            vol_cond = self.data.volume[0] > self.vol_ma[0] * self.params.vol_mult
            price_cond = self.data.close[0] >= self.high_roll[0]
            
            if vol_cond and price_cond:
                self.buy()
                self.trades_log.append(('BUY', self.data.datetime.datetime(0), self.data.close[0]))

        elif pos > 0:
            # EOD
            if self.data.datetime.time() >= datetime.time(15, 0):
                self.close()
                self.trades_log.append(('SELL_EOD', self.data.datetime.datetime(0), self.data.close[0]))
                return

            entry_price = self.position.price
            # Stop
            if self.data.close[0] < entry_price * (1 - self.params.trail_stop):
                self.close()
                self.trades_log.append(('SELL_STOP', self.data.datetime.datetime(0), self.data.close[0]))
            # TP
            elif self.data.close[0] > entry_price * (1 + self.params.tp):
                self.close()
                self.trades_log.append(('SELL_TP', self.data.datetime.datetime(0), self.data.close[0]))

def run_forensic():
    # Load Data
    df = pd.read_csv(FILE_PATH, parse_dates=['ts'])
    target_date = pd.to_datetime(DATE_FILTER).date()
    day_df = df[df['ts'].dt.date == target_date].copy()
    
    if len(day_df) == 0:
        print("No data for date.")
        return

    # Backtrader
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10000000)
    
    data = bt.feeds.PandasData(
        dataname=day_df.set_index('ts'),
        open='open', high='high', low='low', close='close', volume='volume',
        timeframe=bt.TimeFrame.Minutes
    )
    cerebro.adddata(data)
    cerebro.addstrategy(ForensicStrategy)
    
    print(f"Running Forensic Analysis on {DATE_FILTER} for 424870...")
    strat = cerebro.run()[0]
    
    # Plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(day_df['ts'], day_df['close'], label='Price', color='gray', alpha=0.5)
    
    # Plot Trades
    for action, time, price in strat.trades_log:
        color = 'red' if 'SELL' in action else 'green'
        marker = '^' if 'BUY' in action else 'v'
        ax.scatter(time, price, color=color, marker=marker, s=100, label=action if action not in [l.get_label() for l in ax.get_lines()] else "")
        ax.annotate(action, (time, price), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8, color=color)
        
    ax.set_title(f"Forensic Analysis: Why we missed Hero 424870 ({DATE_FILTER})")
    ax.legend()
    plt.grid(True)
    
    os.makedirs(os.path.dirname(OUT_CHART), exist_ok=True)
    plt.savefig(OUT_CHART)
    print(f"Saved chart: {OUT_CHART}")
    
    # Print Log
    print("\n=== Trade Log ===")
    for t in strat.trades_log:
        print(t)

if __name__ == "__main__":
    run_forensic()
