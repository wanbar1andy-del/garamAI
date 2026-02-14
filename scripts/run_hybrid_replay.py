
import pandas as pd
import glob
import os
import backtrader as bt
import datetime as dt


class IntradayHeroStrategyHybrid(bt.Strategy):
    """
    Hybrid Strategy (Champion Candidate)
    - Vol: 2.0 (Aggressive Entry)
    - TP: 5% (Conservative Exit)
    - Defense: V2 (Safety Net)
    """
    params = (
        ("warmup", 30),
        ("breakout_lookback", 30),
        ("vol_ma_period", 20),
        ("vol_mult", 2.0),              # Aggressive Entry
        ("trail_stop", 0.01),
        ("take_profit", 0.05),          # Conservative Exit
        ("entry_cash_frac", 0.10),
        ("max_new_entries_per_bar", 1),
        
        # Defense V2
        ("daily_loss_limit_pct", 0.015), # -1.5%
        ("max_consecutive_losses", 5),   # 5x
        ("time_stop_hard_mins", 100),    # 100m
        ("time_stop_soft_mins", 60),     # 60m
        ("soft_stop_mfe_trigger", 0.007),# if MFE < 0.7% in 60m -> Close
        ("cooldown_mins", 10),           # 10m (Loss Only)
        
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
        self.last_exit_time = {} 
        self.last_exit_pnl = {} 
        self.highest_price_in_trade = {} 

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

        # Review Positions (Time Stop V2)
        for d in self.datas:
            pos = self.getposition(d).size
            if pos > 0:
                high_now = d.high[0]
                if d not in self.highest_price_in_trade:
                    self.highest_price_in_trade[d] = high_now
                else:
                    self.highest_price_in_trade[d] = max(self.highest_price_in_trade[d], high_now)

                entry_t = self.entry_times.get(d)
                entry_p = self.getposition(d).price
                if entry_t:
                    duration = (now_dt - entry_t).total_seconds() / 60
                    
                    if duration >= self.p.time_stop_hard_mins:
                        self.log(f"[HARD TIME STOP] {d._name} {duration:.0f}m")
                        self.close(data=d)
                        continue
                        
                    if duration >= self.p.time_stop_soft_mins:
                        max_price = self.highest_price_in_trade[d]
                        mfe = (max_price - entry_p) / entry_p
                        if mfe < self.p.soft_stop_mfe_trigger:
                            self.log(f"[SOFT TIME STOP] {d._name} {duration:.0f}m MFE={mfe*100:.2f}%")
                            self.close(data=d)
                            continue

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
            
            # Cooldown (Loss Only)
            last_exit = self.last_exit_time.get(d)
            last_pnl = self.last_exit_pnl.get(d, 0)
            if last_exit and last_pnl < 0: 
                if (now_dt - last_exit).total_seconds() / 60 < self.p.cooldown_mins:
                    continue

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
                    self.highest_price_in_trade[d] = d.close[0]

    def notify_trade(self, trade):
        if trade.isclosed:
            self.last_exit_time[trade.data] = self.datas[0].datetime.datetime(0)
            self.last_exit_pnl[trade.data] = trade.pnl
            if trade.pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0

def run_hybrid_replay():
    dates = ["2025-12-09", "2025-12-10", "2025-12-11", "2025-12-12", "2026-01-02"]
    data_dir = "GARAM_Data/5day_replay_kst"

    current_cash = 10_000_000.0
    equity_curve = []

    for date_str in dates:
        print(f"\n--- Hybrid Sim {date_str} (Start: {current_cash:,.0f}) ---")
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(current_cash)
        cerebro.broker.setcommission(commission=0.0023)

        target_date = pd.to_datetime(date_str).date()
        files = glob.glob(os.path.join(data_dir, "*.csv"))
        loaded = 0
        for f in files:
            try:
                df = pd.read_csv(f, parse_dates=['ts'])
                day_df = df[df['ts'].dt.date == target_date].copy()
                if len(day_df) < 30: continue
                day_df.set_index('ts', inplace=True)
                data = bt.feeds.PandasData(dataname=day_df, timeframe=bt.TimeFrame.Minutes)
                data._name = os.path.basename(f).replace(".csv","")
                cerebro.adddata(data)
                loaded += 1
            except: pass
        
        if loaded == 0: continue

        cerebro.addstrategy(IntradayHeroStrategyHybrid)
        strat = cerebro.run()[0]
        
        current_cash = cerebro.broker.getvalue()
        print(f"End: {current_cash:,.0f} (PnL: {(current_cash/cerebro.broker.startingcash - 1)*100:.2f}%)")
        equity_curve.extend(strat.equity_log)

    pd.DataFrame(equity_curve).to_csv("GARAM_Data/5day_equity_hybrid.csv", index=False)
    print("Saved GARAM_Data/5day_equity_hybrid.csv")

if __name__ == "__main__":
    run_hybrid_replay()
