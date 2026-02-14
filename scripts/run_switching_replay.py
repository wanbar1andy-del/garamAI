
import pandas as pd
import glob
import os
import backtrader as bt
import datetime as dt
import numpy as np

class IntradayHeroStrategySwitching(bt.Strategy):
    """
    Phase 36-A: Alpha Mode Switching (User Request)
    - Bear Cap: 70%
    - Daily Loss: -3.5%
    - Switches: Max 6/day, Threshold -0.5%
    - Concentration: PnL > 3% & Rank#1 (3 bars) -> 80%
    """
    params = (
        ("warmup", 30),
        ("breakout_lookback", 30),
        ("vol_ma_period", 20),
        ("vol_mult", 2.0),
        ("trail_stop", 0.01),
        ("take_profit", 0.05), # Base TP
        
        ("max_slots", 5),
        ("bearer_allocation", 0.70),    # Relaxed Defense
        ("bull_allocation", 1.00),
        
        ("switch_threshold_pnl", -0.005), # Aggressive Switch (-0.5%)
        ("max_switches_today", 6),        # Aggressive Switching
        
        ("daily_loss_limit", 0.035),      # -3.5% Daily Limit
        
        ("concentration_trigger_pnl", 0.03), # +3%
        ("concentration_target", 0.80),      # 80% Allocation
        
        ("market_open", dt.time(9, 0)),
        ("market_close", dt.time(15, 30)),
        ("force_exit_at", dt.time(15, 0)),
        ("debug", True),
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
        self.concentrated_positions = set()
        self.rank_history = [] # List of [Symbol, Symbol, Symbol...] (Top 1 per bar)
        self.trade_disabled_today = False
        self.start_cash = 0

    def start(self):
        self.start_cash = self.broker.getcash()
        self.switches_today_count = 0
        self.current_day = None

    def log(self, msg):
        if self.p.debug:
            print(msg)

    def next(self):
        dt_now = self.datas[0].datetime.date(0)
        now_time = self.datas[0].datetime.time(0)
        
        # New Day Reset
        if self.current_day != dt_now:
            self.current_day = dt_now
            self.switches_today_count = 0
            self.trade_disabled_today = False
            self.rank_history = []
            self.concentrated_positions = set()
            self.start_cash = self.broker.getvalue() # Reset Daily Basis? No, Start is Session Start.
                                                     # Wait, Daily Loss Limit needs "Start of Day Equity".
                                                     # In Backtrader, easy way is to capture it here.
            
            # Proper Daily Loss Limit Base
            self.daily_start_equity = self.broker.getvalue()
        
        current_value = self.broker.getvalue()
        cash = self.broker.getcash()
        
        # 0. Daily Loss Limit Check
        daily_pnl_pct = (current_value - self.daily_start_equity) / self.daily_start_equity
        if not self.trade_disabled_today and daily_pnl_pct < -self.p.daily_loss_limit:
            self.log(f"[HALT] Daily Loss {-daily_pnl_pct:.2%} > Limit {self.p.daily_loss_limit:.2%}. Stopping.")
            self.trade_disabled_today = True
            # Close All? Optional. User said "Halt". Usually implies Close All to prevent -10%.
            for d in self.datas:
                if self.getposition(d).size != 0: self.close(d)
            return

        if self.trade_disabled_today:
            return

        # 1. Regime & Positions
        total_unrealized = 0
        positions = []
        for d in self.datas:
            pos = self.getposition(d)
            if pos.size != 0:
                pnl = (d.close[0] - pos.price) / pos.price * (1 if pos.size > 0 else -1)
                total_unrealized += (d.close[0] - pos.price) * pos.size
                positions.append((d, pnl, pos))
        
        avg_pnl = total_unrealized / current_value if len(positions) > 0 else 0
        is_bear = avg_pnl < -0.005
        max_allowed_equity = current_value * (self.p.bearer_allocation if is_bear else self.p.bull_allocation)
        current_exposure = current_value - cash
        
        # 2. Hero Candidates Scan (Rank Calc)
        candidates = []
        for d in self.datas:
            if len(d) < self.p.warmup: continue
            
            prev_vol = self.inds[d]["vol_ma"][-1]
            prev_high = self.inds[d]["high_roll"][-1]
            
            # Basic Signal (No Filters)
            if np.isnan(prev_vol) or prev_vol == 0: continue
             
            if d.volume[0] > prev_vol * self.p.vol_mult and d.close[0] >= prev_high:
                score = d.volume[0] / prev_vol
                candidates.append((d, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top_hero = candidates[0][0] if len(candidates) > 0 else None
        
        # Track Rank History (Last 3 bars)
        self.rank_history.append(top_hero)
        if len(self.rank_history) > 3: self.rank_history.pop(0)
        
        # Check Hero Status: Top 1 for 3 bars
        def is_confirmed_hero(data):
            if len(self.rank_history) < 3: return False
            return all(h == data for h in self.rank_history)

        # 3. Risk & Concentration Management
        for d, pnl, pos in positions:
            
            # Concentration Check
            # Rules: PnL > 3% AND Rank#1 for 3 bars
            if pnl > self.p.concentration_trigger_pnl:
                if is_confirmed_hero(d) and d not in self.concentrated_positions:
                    # SCALE UP to 80%
                    self.log(f"[CONCENTRATE] {d._name} PnL={pnl:.2%} & Rank#1 confirmed. Scaling to 80%.")
                    
                    target_val = current_value * self.p.concentration_target
                    current_pos_val = pos.size * d.close[0]
                    needed = target_val - current_pos_val
                    
                    if needed > 0 and cash > needed:
                        size = int(needed / d.close[0])
                        self.buy(data=d, size=size)
                        self.concentrated_positions.add(d)
            
            # Standard Exits
            if d.close[0] < pos.price * (1 - self.p.trail_stop):
                 self.close(data=d)
                 if d in self.concentrated_positions: self.concentrated_positions.remove(d)
            elif d.close[0] >= pos.price * (1 + self.p.take_profit):
                 self.close(data=d)
                 if d in self.concentrated_positions: self.concentrated_positions.remove(d)

        # 4. Entry / Switching
        if now_time >= dt.time(14, 30): return 

        slot_size = current_value / self.p.max_slots
        
        for cand_d, score in candidates:
            if self.getposition(cand_d).size != 0: continue # Already hold
            
            # Allocation
            active_count = len(positions)
            if active_count < self.p.max_slots:
                # Fill Slot
                if current_exposure + slot_size <= max_allowed_equity:
                     size = int(slot_size / cand_d.close[0])
                     if size > 0:
                         self.log(f"[BUY] {cand_d._name} EstPrice={cand_d.close[0]}")
                         self.buy(data=cand_d, size=size)
                         current_exposure += slot_size
            else:
                # Switching
                if self.switches_today_count >= self.p.max_switches_today: continue
                
                # Find Weakest
                positions.sort(key=lambda x: x[1])
                weakest_d, weakest_pnl, weakest_pos = positions[0]
                
                # Protect Confirmed Heroes from being switched out
                if weakest_d in self.concentrated_positions:
                    # If the weakest is a Hero, maybe we shouldn't switch it unless it's really bad?
                    # But if PnL is low enough to be weak (-0.5%), it's probably failing Hero status.
                    # Standard logic applies.
                    pass

                if weakest_pnl < self.p.switch_threshold_pnl:
                     self.log(f"[SWITCH] Selling {weakest_d._name} ({weakest_pnl:.2%}) for {cand_d._name}")
                     self.close(data=weakest_d)
                     if weakest_d in self.concentrated_positions: self.concentrated_positions.remove(weakest_d)
                     
                     size = int(slot_size / cand_d.close[0])
                     if size > 0:
                         self.buy(data=cand_d, size=size)
                         self.switches_today_count += 1

    def notify_trade(self, trade):
        if trade.isclosed:
            if trade.data in self.concentrated_positions:
                self.concentrated_positions.remove(trade.data)

def run_switching_replay():
    data_dir = "GARAM_Data/60day_replay_kst"
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    print(f"Loading {len(files)} files into memory...")
    
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
    
    print(f"Running Switching Sim (Alpha Mode) on {len(dates)} days...")
    
    current_cash = 10_000_000.0
    equity_curve = []

    for i, target_date in enumerate(dates):
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"--- Sim {i+1}/{len(dates)} : {date_str} (Start: {current_cash:,.0f}) ---", end="\r")
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(current_cash)
        cerebro.broker.setcommission(commission=0.0023)

        added = 0
        for sym, df in data_cache.items():
            day_df = df[df['date'] == target_date].copy()
            if len(day_df) < 30: continue
            day_df.set_index('ts', inplace=True)
            data = bt.feeds.PandasData(dataname=day_df, timeframe=bt.TimeFrame.Minutes)
            data._name = sym
            cerebro.adddata(data)
            added += 1
        
        if added == 0: continue

        cerebro.addstrategy(IntradayHeroStrategySwitching)
        strat = cerebro.run()[0]
        current_cash = cerebro.broker.getvalue()
        equity_curve.extend(strat.equity_log)

    pd.DataFrame(equity_curve).to_csv("GARAM_Data/switching_equity.csv", index=False)
    print("\nSaved GARAM_Data/switching_equity.csv")
    print(f"Final Equity: {current_cash:,.0f}")

if __name__ == "__main__":
    run_switching_replay()
