import pandas as pd
import numpy as np
from pathlib import Path
import sys
import itertools
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class GridSearchSimulator:
    def __init__(self, start_date, end_date):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        
        # Pre-load data to speed up 144 runs
        print("Pre-loading data...")
        self.price_map_daily = {} # {date_str: {symbol: df}}
        current = self.start_date
        while current <= self.end_date:
            ymd = current.strftime("%Y%m%d")
            self.price_map_daily[ymd] = self.load_day_data(ymd)
            current += timedelta(days=1)
            
        self.results = []
        
    def load_day_data(self, ymd):
        # Load all potential candidates
        rank_path = project_root / "results" / "labels" / f"day={ymd}" / "hero_rank.csv"
        if not rank_path.exists(): return {}
        
        candidates = pd.read_csv(rank_path)['symbol'].unique()
        day_map = {}
        for sym in candidates:
            p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
            if p.exists():
                try:
                    df = pd.read_csv(p, usecols=['date', 'close', 'volume'])
                    df = df[df['date'].astype(str).str.startswith(ymd)].copy()
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
                    df.dropna(subset=['date', 'close'], inplace=True)
                    df.set_index('date', inplace=True)
                    if not df.empty:
                        day_map[str(sym).zfill(6)] = df
                except: pass
        return day_map

    def run_grid(self):
        # Define Grid
        param_grid = {
            "entry_roc": [-0.001, -0.002, -0.003, -0.005], # Pullback Depth
            "entry_vol": [0.8, 1.0, 1.5, 2.0], # Volume Strength
            "exit_sl": [-0.002, -0.005, -0.010], # Stop Loss Widening
            "exit_tp": [0.005, 0.010, 0.020] # Take Profit Target
        }
        
        keys, values = zip(*param_grid.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        print(f"Starting Grid Search: {len(combinations)} combinations")
        
        for i, params in enumerate(combinations):
            if i % 10 == 0: print(f"  Simulating {i}/{len(combinations)}...")
            res = self.simulate_scenario(params)
            res.update(params)
            self.results.append(res)
            
        self.save_results()

    def simulate_scenario(self, params):
        # Fast simulation logic
        capital = 10_000_000.0
        shares = 0
        holding_symbol = None
        entry_price = 0.0
        
        trades_count = 0
        sum_net_pnl = 0.0
        
        cost_rate = 0.0010 # 10bps
        
        current = self.start_date
        while current <= self.end_date:
            ymd = current.strftime("%Y%m%d")
            day_data = self.price_map_daily.get(ymd, {})
            if not day_data:
                current += timedelta(days=1)
                continue
                
            session_idx = pd.date_range(f"{ymd} 09:00", f"{ymd} 15:30", freq="1T")
            
            for t in session_idx:
                # 1. Check Exit
                if holding_symbol:
                    df = day_data.get(holding_symbol)
                    if df is not None and t in df.index:
                        p_now = df['close'].at[t]
                        
                        # Features for Exit
                        # VWAP Div approx
                        # SL Check
                        
                        # Simplified feature calc for speed
                        # ROC 5m
                        t_prev_5 = t - timedelta(minutes=5)
                        if t_prev_5 in df.index:
                            p_prev = df['close'].at[t_prev_5]
                            roc_5m = (p_now / p_prev) - 1.0
                        else:
                            roc_5m = 0.0
                            
                        # VWAP (Daily cumsum approx)
                        # Assume we just check price vs entry for TP for speed? 
                        # Or stick to logic: VWAP Div.
                        # Let's simple logical equivalent: Price > Entry * (1+TP)? No, policy said VWAP.
                        # We must calc VWAP.
                        # Fast approximation: Day VWAP
                        vol_now = df['volume'].at[t]
                        # Just use simple Cumulative from open to now
                        try:
                            # This slice is slow inside 144 loops * minutes.
                            # But needed for accuracy.
                            # Optimization: Use price deviation from MA?
                            # Stick to spec for now.
                            # To speed up, maybe just check p_now vs entry_price profit?
                            # Policy V1 was "VWAP Div > 0.5%".
                            # Let's impl:
                            day_slice = df.loc[:t]
                            cum_pv = (day_slice['close'] * day_slice['volume']).sum()
                            cum_vol = day_slice['volume'].sum()
                            vwap = cum_pv / cum_vol if cum_vol > 0 else p_now
                            vwap_div = (p_now / vwap) - 1.0
                        except: vwap_div = 0
                        
                        should_exit = False
                        if vwap_div > params['exit_tp']: should_exit = True
                        elif roc_5m < params['exit_sl']: should_exit = True
                        
                        if should_exit:
                            # EXECUTE SELL
                            gross_val = shares * p_now
                            cost = gross_val * (cost_rate/2)
                            net = gross_val - cost
                            
                            pnl = (p_now - entry_price) * shares - cost # Entry cost already paid
                            # Wait, correct logic:
                            # Buy: Cap -= Cost. Shares = Cap/Price. Net PnL = -Cost.
                            # Sell: Cap = Shares*Price - Cost. Net PnL = (Price-Entry)*Shares - Cost.
                            # Total PnL accumulates Net Pnl of Buy(-Cost) + Sell(Realized - Cost).
                            
                            # Simplified PnL tracking:
                            # Trade PnL = (Exit - Entry)*Shares - (EntryCost + ExitCost)
                            entry_cost = (entry_price * shares) * (cost_rate/2)
                            trade_net_pnl = (p_now - entry_price) * shares - entry_cost - cost
                            
                            sum_net_pnl += trade_net_pnl
                            capital = net
                            shares = 0
                            holding_symbol = None
                            trades_count += 1
                            
                # 2. Check Entry
                if not holding_symbol:
                    # Scan candidates
                    # Need Top-5 Rank
                    # Rank = 30m ret
                    t_prev_30 = t - timedelta(minutes=30)
                    scores = []
                    
                    for sym, df in day_data.items():
                        if t not in df.index: continue
                        try:
                            p_now = df['close'].at[t]
                            if t_prev_30 in df.index:
                                p_prev = df['close'].at[t_prev_30]
                                ret_30 = (p_now / p_prev) - 1.0
                            else: ret_30 = -999
                            scores.append((sym, ret_30, p_now, df))
                        except: pass
                        
                    scores.sort(key=lambda x: x[1], reverse=True)
                    top_5 = scores[:5]
                    
                    for sym, _, p_now, df in top_5:
                        # Check Entry Conds
                        # ROC < entry_roc
                        # Vol Accel > entry_vol
                        t_prev_5 = t - timedelta(minutes=5)
                        if t_prev_5 in df.index:
                            roc_5m = (p_now / df['close'].at[t_prev_5]) - 1.0
                        else: roc_5m = 0
                        
                        # Vol Accel
                        # 10m mean
                        t_start_Win = t - timedelta(minutes=10)
                        vol_slice = df['volume'].loc[t_start_Win:t]
                        v_ma = vol_slice.mean()
                        v_now = df['volume'].at[t]
                        vol_accel = v_now / v_ma if v_ma > 0 else 0
                        
                        if roc_5m < params['entry_roc'] and vol_accel >= params['entry_vol']:
                            # BUY
                            cost = capital * (cost_rate/2)
                            net_cap = capital - cost
                            shares = net_cap / p_now
                            entry_price = p_now
                            holding_symbol = sym
                            capital = 0 # Invested
                            
                            sum_net_pnl -= cost # Entry fee
                            break
                            
            current += timedelta(days=1)
            
        # End of Sim
        # Force Close
        if holding_symbol:
            # Assume last known price or 0
            # Just ignore for summary or penalize?
            # Let's MTM
            pass 
        
        final_eq = 10_000_000.0 + sum_net_pnl
        ret = (final_eq / 10_000_000.0) - 1.0
        
        return {
            "return": ret,
            "trades": trades_count,
            "final_equity": final_eq
        }
        
    def save_results(self):
        df = pd.DataFrame(self.results)
        out_path = project_root / "results" / "optimization" / "grid_search_week1.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        
        # Print Best
        print("\n[Grid Search Results]")
        best = df.sort_values('return', ascending=False).iloc[0]
        print(f"Best Param: {best.to_dict()}")
        print(f"Best Return: {best['return']*100:.2f}%")
        print(f"Trades: {best['trades']}")

if __name__ == "__main__":
    sim = GridSearchSimulator("2025-12-15", "2025-12-19")
    sim.run_grid()
