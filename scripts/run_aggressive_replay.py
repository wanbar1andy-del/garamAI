
import pandas as pd
import glob
import os
import backtrader as bt
import datetime as dt


class IntradayHeroStrategyAggressive(bt.Strategy):
    """
    Aggressive Profit Mode (Push Harder)
    - Vol: 2.0 (More Entries)
    - TP: 10% (Big Wins)
    - Defense: Minimal (Daily Limit -2.5%, No Time Stop, No Cooldown)
    """
    params = (
        ("warmup", 30),
        ("breakout_lookback", 30),
        ("vol_ma_period", 20),
        ("vol_mult", 2.0),              # Aggressive Entry
        ("trail_stop", 0.01),           # Tight Stop remains (Risk Control)
        ("take_profit", 0.10),          # Aggressive Reward
        ("entry_cash_frac", 0.10),
        ("max_new_entries_per_bar", 1),
        
        # Minimal Defense
        ("daily_loss_limit_pct", 0.025), # -2.5% (Wide Room)
        ("max_consecutive_losses", 10),  # Effectively Off
        ("time_stop_hard_mins", 9999),   # Off
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
        self.trade_disabled_today = False

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

        # 1. Daily Loss Limit (Wide)
        if not self.trade_disabled_today and self.daily_pnl <= -self.p.daily_loss_limit_pct:
            self.log(f"Daily Loss Limit Hit ({self.daily_pnl*100:.2f}%). Force OFF.")
            self.trade_disabled_today = True
            for d in self.datas:
                 if self.getposition(d).size != 0:
                     self.close(data=d)
            return

        # EOD Exit
        if now_time >= self.p.force_exit_at:
            for d in self.datas:
                if self.getposition(d).size != 0:
                    self.close(data=d)
            return

        # Review Positions
        for d in self.datas:
            pos = self.getposition(d).size
            if pos > 0:
                entry_price = self.getposition(d).price
                # Trail Stop / TP
                if d.close[0] < entry_price * (1 - self.p.trail_stop):
                    self.close(data=d)
                elif d.close[0] >= entry_price * (1 + self.p.take_profit):
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

def run_aggressive_replay():
    dates = ["2025-12-09", "2025-12-10", "2025-12-11", "2025-12-12", "2026-01-02"]
    data_dir = "GARAM_Data/5day_replay_kst"

    current_cash = 10_000_000.0
    equity_curve = []

    for date_str in dates:
        print(f"\n--- Aggressive Sim {date_str} (Start: {current_cash:,.0f}) ---")
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

        cerebro.addstrategy(IntradayHeroStrategyAggressive)
        strat = cerebro.run()[0]
        
        current_cash = cerebro.broker.getvalue()
        print(f"End: {current_cash:,.0f} (PnL: {(current_cash/cerebro.broker.startingcash - 1)*100:.2f}%)")
        equity_curve.extend(strat.equity_log)

    pd.DataFrame(equity_curve).to_csv("GARAM_Data/5day_equity_aggressive.csv", index=False)
    print("Saved GARAM_Data/5day_equity_aggressive.csv")

if __name__ == "__main__":
    run_aggressive_replay()
