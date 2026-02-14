
import pandas as pd
import glob
import os
import backtrader as bt
import datetime as dt


class IntradayHeroStrategy60Day(bt.Strategy):
    """
    60-Day Verification Strategy (Baseline + Emergency Defense)
    - Vol: 3.0 (Selective Entry)
    - TP: 5% (Conservative Exit)
    - Defense V3: Minimal (Daily -2.5%, Consec 10, Time 120m)
    """
    params = (
        ("warmup", 30),
        ("breakout_lookback", 30),
        ("vol_ma_period", 20),
        ("vol_mult", 3.0),              # Baseline Selective
        ("trail_stop", 0.01),
        ("take_profit", 0.05),          # Conservative
        ("entry_cash_frac", 0.10),
        ("max_new_entries_per_bar", 1),
        
        # Defense V3 (Emergency Only)
        ("daily_loss_limit_pct", 0.025), # -2.5%
        ("max_consecutive_losses", 10),  # 10x
        ("time_stop_hard_mins", 120),    # 120m
        ("time_stop_soft_mins", 9999),   # Off
        ("cooldown_mins", 0),            # Off
        
        ("force_exit_at", dt.time(15, 0)),
        ("market_open", dt.time(9, 0)),
        ("market_close", dt.time(15, 30)),
        ("debug", False),
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                "vol_ma": bt.indicators.SMA(d.volume, period=self.p.vol_ma_period),
                "high_roll": bt.indicators.Highest(d.high, period=self.p.breakout_lookback),
            }

        self.equity_log = []
        self._entered_this_bar = 0
        
        # Defense State
        self.start_cash = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.trade_disabled_today = False
        
        # Per Symbol State
        self.entry_times = {} 

    def start(self):
        self.start_cash = self.broker.getcash()

    def log(self, msg):
        if self.p.debug:
            print(msg)

    def next(self):
        self._entered_this_bar = 0
        current_value = self.broker.getvalue()
        
        daily_pnl_amt = current_value - self.start_cash
        self.daily_pnl = daily_pnl_amt / self.start_cash
        
        self.equity_log.append({
            "ts": self.datas[0].datetime.datetime(0),
            "Total_Equity": float(current_value),
            "Daily_PnL_Pct": self.daily_pnl
        })

        now_time = self.datas[0].datetime.time(0)
        now_dt = self.datas[0].datetime.datetime(0)

        # 1. Daily Loss Limit
        if not self.trade_disabled_today and self.daily_pnl <= -self.p.daily_loss_limit_pct:
            self.log(f"Daily Loss Limit Hit ({self.daily_pnl*100:.2f}%). Force OFF.")
            self.trade_disabled_today = True
            for d in self.datas:
                 if self.getposition(d).size != 0:
                     self.close(data=d)
            return

        # 2. Consecutive Loss Brake
        if not self.trade_disabled_today and self.consecutive_losses >= self.p.max_consecutive_losses:
             self.log(f"Consecutive Loss Limit ({self.consecutive_losses}). Force OFF.")
             self.trade_disabled_today = True
             return

        # EOD Exit
        if now_time >= self.p.force_exit_at:
            for d in self.datas:
                if self.getposition(d).size != 0:
                    self.close(data=d)
            return

        # Review Positions (Time Stop 120m)
        for d in self.datas:
            pos = self.getposition(d).size
            if pos > 0:
                entry_t = self.entry_times.get(d)
                entry_p = self.getposition(d).price
                if entry_t:
                    duration = (now_dt - entry_t).total_seconds() / 60
                    if duration >= self.p.time_stop_hard_mins:
                        self.close(data=d)
                        continue

                # Trail Stop / TP
                if d.close[0] < entry_p * (1 - self.p.trail_stop):
                    self.close(data=d)
                elif d.close[0] >= entry_p * (1 + self.p.take_profit):
                    self.close(data=d)

        # New Entries
        if self.trade_disabled_today: return
        if now_time >= dt.time(14, 30): return

        for d in self.datas:
            if self._entered_this_bar >= self.p.max_new_entries_per_bar: break
            if len(d) < self.p.warmup: continue
            if self.getposition(d).size != 0: continue
            
            # Signal Check
            prev_vol = self.inds[d]["vol_ma"][-1]
            prev_high = self.inds[d]["high_roll"][-1]
            if not prev_vol or not prev_high: continue
            
            if d.volume[0] > prev_vol * self.p.vol_mult and d.close[0] >= prev_high:
                budget = current_value * self.p.entry_cash_frac
                cash = self.broker.getcash()
                budget = min(budget, cash)
                size = int(budget / d.close[0])
                
                if size > 0:
                    self.buy(data=d, size=size)
                    self._entered_this_bar += 1
                    self.entry_times[d] = now_dt

    def notify_trade(self, trade):
        if trade.isclosed:
            if trade.pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0

def run_60day_replay_optimized():
    data_dir = "GARAM_Data/60day_replay_kst"
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    print(f"Loading {len(files)} files into memory...")
    
    # Load all data into memory dict: symbol -> DataFrame
    data_cache = {}
    all_dates = set()
    
    for f in files:
        try:
            df = pd.read_csv(f, parse_dates=['ts'])
            if df.empty: continue
            df['date'] = df['ts'].dt.date
            sym = os.path.basename(f).replace(".csv", "")
            data_cache[sym] = df
            all_dates.update(df['date'].unique())
        except: pass
        
    dates = sorted(list(all_dates))
    print(f"Loaded {len(data_cache)} symbols. Found {len(dates)} unique dates.")
    
    # LIMIT FOR INTERACTIVE SESSION: 10 Days
    # dates = dates[:10] 
    # Uncomment above line to limit.
    # Currently running FULL.
    # Wait, I need to limit it NOW.
    # dates = dates[:10] # RESTORED TO FULL
    print(f"Running FULL verification on {len(dates)} days...")
    
    current_cash = 10_000_000.0
    equity_curve = []

    # Iterate Run
    for i, target_date in enumerate(dates):
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"--- Sim {i+1}/{len(dates)} : {date_str} (Start: {current_cash:,.0f}) ---", end="\r")
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(current_cash)
        cerebro.broker.setcommission(commission=0.0023)

        added = 0
        for sym, df in data_cache.items():
            # Filter in memory
            day_df = df[df['date'] == target_date].copy()
            if len(day_df) < 30: continue
            
            day_df.set_index('ts', inplace=True)
            data = bt.feeds.PandasData(dataname=day_df, timeframe=bt.TimeFrame.Minutes)
            data._name = sym
            cerebro.adddata(data)
            added += 1
            
        if added == 0:
            print(f"\nSkip {date_str} (No Data)")
            continue

        cerebro.addstrategy(IntradayHeroStrategy60Day)
        strat = cerebro.run()[0]
        
        current_cash = cerebro.broker.getvalue()
        equity_curve.extend(strat.equity_log)

    # Save
    pd.DataFrame(equity_curve).to_csv("GARAM_Data/60day_equity.csv", index=False)
    print("\nSaved GARAM_Data/60day_equity.csv")
    print(f"Final Equity: {current_cash:,.0f}")

if __name__ == "__main__":
    run_60day_replay_optimized()
