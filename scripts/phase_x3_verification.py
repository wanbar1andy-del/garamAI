"""
Phase X-3: 60-Day Verification
Compare V0 (re-entry allowed) vs V1 (1-trade-per-symbol-per-day)

Goal: Prove that blocking re-entry fixes the "peak re-entry" leakage.
"""
import pandas as pd
import glob
import os
import backtrader as bt
import datetime as dt
import numpy as np

class IntradayHeroV0(bt.Strategy):
    """V0: Original - Re-entry ALLOWED"""
    params = (
        ("warmup", 30),
        ("breakout_lookback", 30),
        ("vol_ma_period", 20),
        ("vol_mult", 2.0),
        ("trail_stop", 0.01),
        ("take_profit", 0.05),
        ("max_slots", 5),
        ("bearer_allocation", 0.50),
        ("bull_allocation", 1.00),
        ("debug", False),
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                "vol_ma": bt.indicators.SMA(d.volume, period=self.p.vol_ma_period),
                "high_roll": bt.indicators.Highest(d.high, period=self.p.breakout_lookback),
            }
        self.current_day = None

    def next(self):
        dt_now = self.datas[0].datetime.date(0)
        now_time = self.datas[0].datetime.time(0)
        
        if self.current_day != dt_now:
            self.current_day = dt_now
        
        if now_time >= dt.time(14, 30): return
        
        current_value = self.broker.getvalue()
        cash = self.broker.getcash()
        
        # Positions
        positions = []
        for d in self.datas:
            pos = self.getposition(d)
            if pos.size != 0:
                pnl = (d.close[0] - pos.price) / pos.price
                positions.append((d, pnl, pos))
                
                # Exit logic
                if pnl <= -self.p.trail_stop:
                    self.close(data=d)
                elif pnl >= self.p.take_profit:
                    self.close(data=d)
        
        # Entry
        candidates = []
        for d in self.datas:
            if len(d) < self.p.warmup: continue
            if self.getposition(d).size != 0: continue
            
            prev_vol = self.inds[d]["vol_ma"][-1]
            prev_high = self.inds[d]["high_roll"][-1]
            
            if np.isnan(prev_vol) or prev_vol == 0: continue
             
            if d.volume[0] > prev_vol * self.p.vol_mult and d.close[0] >= prev_high:
                score = d.volume[0] / prev_vol
                candidates.append((d, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        slot_size = current_value / self.p.max_slots
        current_exposure = current_value - cash
        max_exposure = current_value * self.p.bearer_allocation
        
        for cand_d, score in candidates[:self.p.max_slots]:
            if len(positions) >= self.p.max_slots: break
            if current_exposure + slot_size > max_exposure: break
            
            size = int(slot_size / cand_d.close[0])
            if size > 0:
                self.buy(data=cand_d, size=size)
                current_exposure += slot_size
                positions.append((cand_d, 0, None))


class IntradayHeroV1(bt.Strategy):
    """V1: One-Shot - Re-entry BLOCKED (1 trade per symbol per day)"""
    params = (
        ("warmup", 30),
        ("breakout_lookback", 30),
        ("vol_ma_period", 20),
        ("vol_mult", 2.0),
        ("trail_stop", 0.01),
        ("take_profit", 0.05),
        ("max_slots", 5),
        ("bearer_allocation", 0.50),
        ("bull_allocation", 1.00),
        ("debug", False),
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                "vol_ma": bt.indicators.SMA(d.volume, period=self.p.vol_ma_period),
                "high_roll": bt.indicators.Highest(d.high, period=self.p.breakout_lookback),
            }
        self.current_day = None
        self.traded_today = set()  # P0 PATCH: Track traded symbols

    def next(self):
        dt_now = self.datas[0].datetime.date(0)
        now_time = self.datas[0].datetime.time(0)
        
        # Day change: Clear traded set
        if self.current_day != dt_now:
            self.current_day = dt_now
            self.traded_today.clear()  # P0 PATCH: Reset daily
        
        if now_time >= dt.time(14, 30): return
        
        current_value = self.broker.getvalue()
        cash = self.broker.getcash()
        
        # Positions
        positions = []
        for d in self.datas:
            pos = self.getposition(d)
            if pos.size != 0:
                pnl = (d.close[0] - pos.price) / pos.price
                positions.append((d, pnl, pos))
                
                # Exit logic
                if pnl <= -self.p.trail_stop:
                    self.close(data=d)
                elif pnl >= self.p.take_profit:
                    self.close(data=d)
        
        # Entry
        candidates = []
        for d in self.datas:
            if len(d) < self.p.warmup: continue
            if self.getposition(d).size != 0: continue
            if d._name in self.traded_today: continue  # P0 PATCH: Skip if already traded
            
            prev_vol = self.inds[d]["vol_ma"][-1]
            prev_high = self.inds[d]["high_roll"][-1]
            
            if np.isnan(prev_vol) or prev_vol == 0: continue
             
            if d.volume[0] > prev_vol * self.p.vol_mult and d.close[0] >= prev_high:
                score = d.volume[0] / prev_vol
                candidates.append((d, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        slot_size = current_value / self.p.max_slots
        current_exposure = current_value - cash
        max_exposure = current_value * self.p.bearer_allocation
        
        for cand_d, score in candidates[:self.p.max_slots]:
            if len(positions) >= self.p.max_slots: break
            if current_exposure + slot_size > max_exposure: break
            
            size = int(slot_size / cand_d.close[0])
            if size > 0:
                self.buy(data=cand_d, size=size)
                self.traded_today.add(cand_d._name)  # P0 PATCH: Mark as traded
                current_exposure += slot_size
                positions.append((cand_d, 0, None))


def run_version(strategy_class, version_name):
    data_dir = "GARAM_Data/60day_replay_kst"
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    
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
    
    current_cash = 10_000_000.0
    
    for i, target_date in enumerate(dates):
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

        cerebro.addstrategy(strategy_class)
        cerebro.run()
        current_cash = cerebro.broker.getvalue()
    
    return current_cash


def main():
    print("="*60)
    print("PHASE X-3: 60-Day Verification (V0 vs V1)")
    print("="*60)
    
    print("\nLoading data...")
    
    print("\n[V0] Running Original (Re-entry Allowed)...")
    final_v0 = run_version(IntradayHeroV0, "V0")
    pnl_v0 = (final_v0 / 10_000_000 - 1) * 100
    print(f"[V0] Final: {final_v0:,.0f} KRW ({pnl_v0:+.2f}%)")
    
    print("\n[V1] Running One-Shot (Re-entry Blocked)...")
    final_v1 = run_version(IntradayHeroV1, "V1")
    pnl_v1 = (final_v1 / 10_000_000 - 1) * 100
    print(f"[V1] Final: {final_v1:,.0f} KRW ({pnl_v1:+.2f}%)")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"V0 (Re-entry Allowed): {pnl_v0:+.2f}%")
    print(f"V1 (One-Shot):         {pnl_v1:+.2f}%")
    print(f"Improvement:           {pnl_v1 - pnl_v0:+.2f}%p")
    
    if pnl_v1 > pnl_v0:
        print("\n✓ ONE-SHOT PATCH IMPROVES PERFORMANCE")
    else:
        print("\n✗ ONE-SHOT PATCH DID NOT HELP (investigate)")


if __name__ == "__main__":
    main()
