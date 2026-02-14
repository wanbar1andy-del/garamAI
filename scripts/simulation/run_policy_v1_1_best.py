import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class PolicyV1Simulator:
    def __init__(self, start_date, end_date, cost_bps=10, execution_delay=1):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.cost_rate = cost_bps / 10000.0
        self.execution_delay = execution_delay 
        
        self.initial_capital = 10_000_000.0
        self.capital = 10_000_000.0
        self.shares = 0
        self.holding_symbol = None
        self.entry_price = 0.0
        
        # Policy V1.1 Best Params (from Grid Search)
        self.ENTRY_RANK_TOP = 5
        self.ENTRY_ROC_MAX = -0.002  # -0.2% (Correct Grid Search Best)
        self.ENTRY_VOL_MIN = 1.5     # 1.5x Volume
        
        self.EXIT_VWAP_DIV_MIN = 0.020 # +2.0% Take Profit
        self.EXIT_ROC_MAX = -0.010     # -1.0% Stop Loss (Wide)
        
        self.trades = []
        
        # Output
        self.out_dir = project_root / "results" / "simulation" / "week1_v1_1"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self):
        print(f"Running Policy v1.1 (Best) Simulation ({self.start_date.date()} ~ {self.end_date.date()})")
        print(f"Params: Entry ROC < {self.ENTRY_ROC_MAX*100}%, Vol > {self.ENTRY_VOL_MIN}x")
        print(f"        Exit TP > {self.EXIT_VWAP_DIV_MIN*100}%, SL < {self.EXIT_ROC_MAX*100}%")
        
        current = self.start_date
        while current <= self.end_date:
            self.run_day(current)
            current += timedelta(days=1)
            
        self.force_close_all()
        self.finalize()

    def run_day(self, date_ts):
        ymd = date_ts.strftime("%Y%m%d")
        print(f"Processing {ymd}...")
        
        rank_path = project_root / "results" / "labels" / f"day={ymd}" / "hero_rank.csv"
        candidate_symbols = []
        if rank_path.exists():
            candidate_symbols = pd.read_csv(rank_path)['symbol'].unique()
            
        price_map = {}
        for sym in candidate_symbols:
            p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
            if p.exists():
                try:
                    df = pd.read_csv(p, usecols=['date', 'close', 'volume'])
                    df = df[df['date'].astype(str).str.startswith(ymd)].copy()
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
                    df.dropna(subset=['date', 'close'], inplace=True)
                    df.set_index('date', inplace=True)
                    price_map[str(sym).zfill(6)] = df
                except: pass
        
        session_idx = pd.date_range(f"{ymd} 09:00", f"{ymd} 15:30", freq="1T")
        
        for t in session_idx:
            candidates_metrics = []
            
            t_prev_30 = t - timedelta(minutes=30)
            t_prev_5 = t - timedelta(minutes=5)
            t_win_start = t - timedelta(minutes=10)
            
            for sym, df in price_map.items():
                if t not in df.index: continue
                try:
                    p_now = df['close'].asof(t)
                    
                    # Rank Metric
                    p_prev_30 = df['close'].asof(t_prev_30) if t_prev_30 in df.index else p_now
                    ret_30 = (p_now / p_prev_30) - 1.0 if p_prev_30 > 0 else -999
                    
                    # ROC 5m
                    p_prev_5 = df['close'].asof(t_prev_5) if t_prev_5 in df.index else p_now
                    roc_5m = (p_now / p_prev_5) - 1.0 if p_prev_5 > 0 else 0
                    
                    # Vol Accel
                    vol_slice = df['volume'].loc[t_win_start:t]
                    curr_vol = df['volume'].at[t]
                    vol_ma = vol_slice.mean()
                    vol_accel = curr_vol / vol_ma if vol_ma > 0 else 0
                    
                    # VWAP Div
                    df_sofar = df.loc[:t]
                    cum_vol = df_sofar['volume'].sum()
                    cum_pv = (df_sofar['close'] * df_sofar['volume']).sum()
                    vwap = cum_pv / cum_vol if cum_vol > 0 else p_now
                    vwap_div = (p_now / vwap) - 1.0
                    
                    candidates_metrics.append({
                        "symbol": sym, "ret_30": ret_30, "roc_5m": roc_5m,
                        "vol_accel": vol_accel, "vwap_div": vwap_div, "price": p_now
                    })
                except: pass
            
            candidates_metrics.sort(key=lambda x: x['ret_30'], reverse=True)
            top_list = candidates_metrics[:self.ENTRY_RANK_TOP]
            
            # EXIT CHECK
            if self.holding_symbol:
                h_metrics = next((x for x in candidates_metrics if x['symbol'] == self.holding_symbol), None)
                if h_metrics:
                    if h_metrics['vwap_div'] > self.EXIT_VWAP_DIV_MIN:
                        self.execute_trade(t, "SELL", self.holding_symbol, "take_profit", price_map)
                    elif h_metrics['roc_5m'] < self.EXIT_ROC_MAX:
                        self.execute_trade(t, "SELL", self.holding_symbol, "stop_loss", price_map)
                else: 
                     self.execute_trade(t, "SELL", self.holding_symbol, "data_missing", price_map)
            
            # ENTRY CHECK
            if not self.holding_symbol:
                for cand in top_list:
                    if (cand['roc_5m'] < self.ENTRY_ROC_MAX) and (cand['vol_accel'] >= self.ENTRY_VOL_MIN):
                        self.execute_trade(t, "BUY", cand['symbol'], "pullback_entry", price_map)
                        break

    def execute_trade(self, time, side, symbol, reason, price_map):
        series = price_map.get(symbol)
        if series is None: return
        exec_time = time + timedelta(minutes=self.execution_delay)
        
        if isinstance(series, pd.Series): exec_price = series.iloc[0]
        else:
            if exec_time in series.index: exec_price = series.loc[exec_time]['close']
            else:
                 idx = series.index.asof(exec_time)
                 if pd.isna(idx): return
                 exec_price = series.loc[idx]['close']
        
        if pd.isna(exec_price) or exec_price <= 0: return

        if side == "BUY":
            cost_amt = self.capital * (self.cost_rate / 2)
            net_capital = self.capital - cost_amt
            self.shares = net_capital / exec_price
            self.entry_price = exec_price
            self.holding_symbol = symbol
            self.capital = 0
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "BUY",
                "qty": self.shares, "price": exec_price, "fee": -cost_amt, 
                "gross_pnl": 0.0, "net_pnl": -cost_amt, 
                "balance": net_capital, "reason": reason
            })
            
        elif side == "SELL":
            gross_val = self.shares * exec_price
            cost_amt = gross_val * (self.cost_rate / 2)
            net_proceeds = gross_val - cost_amt
            gross_pnl = (exec_price - self.entry_price) * self.shares
            net_pnl = gross_pnl - cost_amt 
            self.capital = net_proceeds
            self.shares = 0
            self.holding_symbol = None
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "SELL",
                "qty": self.shares, "price": exec_price, "fee": -cost_amt, 
                "gross_pnl": gross_pnl, "net_pnl": net_pnl, 
                "balance": self.capital, "reason": reason
            })

    def force_close_all(self):
        if self.holding_symbol:
            close_time = self.end_date + timedelta(hours=15, minutes=35)
            self.execute_trade(close_time, "SELL", self.holding_symbol, "force_close", {self.holding_symbol: pd.Series({close_time: self.entry_price})})

    def finalize(self):
        df_trades = pd.DataFrame(self.trades)
        if df_trades.empty:
            print("No trades.")
            return

        out_path = self.out_dir / f"trades_week1_policy_v1_1.csv"
        df_trades.to_csv(out_path, index=False)
        
        end_eq = self.capital
        final_ret = (end_eq / self.initial_capital) - 1.0
        
        print(f"\n[Run Policy v1.1 Complete]")
        print(f"Final Return: {final_ret*100:.2f}%")
        print(f"Trades: {len(df_trades)}")

if __name__ == "__main__":
    sim = PolicyV1Simulator("2025-12-15", "2025-12-19")
    sim.run()
