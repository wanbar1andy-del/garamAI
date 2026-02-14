import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class PolicyV2Simulator:
    def __init__(self, start_date, end_date):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        
        # Policy Params (v1.1 + Multi-Slot)
        self.max_slots = 3
        self.entry_roc = -0.002
        self.entry_vol = 1.5
        self.exit_tp = 0.020
        self.exit_sl = -0.010
        self.cost_rate = 0.0010
        
        # State
        self.initial_capital = 10_000_000.0
        self.capital = 10_000_000.0
        self.positions = {} # {symbol: {qty, entry_price}}
        self.trades = []
        
        # Output
        self.out_dir = project_root / "results" / "simulation" / "month1_v2"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self):
        print(f"Running Policy v2 Simulation (Month-1: {self.start_date.date()} ~ {self.end_date.date()})")
        print(f"Params: ROC < {self.entry_roc}, Vol > {self.entry_vol}, TP > {self.exit_tp}, SL < {self.exit_sl}")
        print(f"Slots: {self.max_slots} (Switching Active)")
        
        current = self.start_date
        while current <= self.end_date:
            self.run_day(current)
            current += timedelta(days=1)
            
        self.finalize()

    def run_day(self, date_ts):
        ymd = date_ts.strftime("%Y%m%d")
        print(f"Processing {ymd}...", end='\r')
        
        # Load Daily Data
        rank_path = project_root / "results" / "labels" / f"day={ymd}" / "hero_rank.csv"
        candidates = []
        if rank_path.exists():
            candidates = pd.read_csv(rank_path)['symbol'].unique()
            
        price_map = {}
        for sym in candidates:
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

        if not price_map: return

        session_idx = pd.date_range(f"{ymd} 09:00", f"{ymd} 15:30", freq="1T")
        
        for t in session_idx:
            # 1. Update & Check Exits
            for sym, pos in list(self.positions.items()):
                df = price_map.get(sym)
                if df is None or t not in df.index: continue
                
                p_now = df['close'].at[t]
                
                # Exit Logic
                # VWAP Div
                df_sofar = df.loc[:t]
                cum_vol = df_sofar['volume'].sum()
                cum_pv = (df_sofar['close'] * df_sofar['volume']).sum()
                vwap = cum_pv / cum_vol if cum_vol > 0 else p_now
                vwap_div = (p_now / vwap) - 1.0
                
                # ROC 5m
                t_prev_5 = t - timedelta(minutes=5)
                p_prev_5 = df['close'].asof(t_prev_5) if t_prev_5 in df.index else p_now
                roc_5m = (p_now / p_prev_5) - 1.0
                
                reason = None
                if vwap_div > self.exit_tp: reason = "take_profit"
                elif roc_5m < self.exit_sl: reason = "stop_loss"
                
                if reason:
                    self.execute_sell(t, sym, p_now, reason)
            
            # 2. Check Entries
            # Scan Candidates
            candidates_metrics = []
            t_prev_30 = t - timedelta(minutes=30)
            t_win_start = t - timedelta(minutes=10)
            
            for sym, df in price_map.items():
                if t not in df.index: continue
                if sym in self.positions: continue
                
                p_now = df['close'].at[t]
                
                # Rank Metric
                p_prev_30 = df['close'].asof(t_prev_30) if t_prev_30 in df.index else p_now
                ret_30 = (p_now / p_prev_30) - 1.0 if p_prev_30 > 0 else -1.0
                
                # Entry Filters
                p_prev_5 = df['close'].asof(t - timedelta(minutes=5)) if (t - timedelta(minutes=5)) in df.index else p_now
                roc_5m = (p_now / p_prev_5) - 1.0
                
                vol_slice = df['volume'].loc[t_win_start:t]
                v_ma = vol_slice.mean()
                v_now = df['volume'].at[t]
                vol_accel = v_now / v_ma if v_ma > 0 else 0
                
                if roc_5m < self.entry_roc and vol_accel >= self.entry_vol:
                     candidates_metrics.append({
                        "symbol": sym, "rank_score": ret_30, "price": p_now
                    })
            
            candidates_metrics.sort(key=lambda x: x['rank_score'], reverse=True)
            
            # Entry Logic (Max 3 Slots)
            for cand in candidates_metrics[:3]:
                if len(self.positions) < self.max_slots:
                    self.execute_buy(t, cand['symbol'], cand['price'], "new_entry")

        # Force Close End of Day
        close_time = pd.Timestamp(f"{ymd} 15:35:00")
        for sym, pos in list(self.positions.items()):
            # Use last price
            df = price_map.get(sym)
            if df is not None and not df.empty:
                last_price = df.iloc[-1]['close']
                self.execute_sell(close_time, sym, last_price, "force_close")
                
    def execute_buy(self, time, symbol, price, reason):
        alloc = self.initial_capital / self.max_slots
        if self.capital < alloc: alloc = self.capital
        
        cost = alloc * (self.cost_rate / 2)
        net_buy = alloc - cost
        qty = net_buy / price
        
        self.positions[symbol] = {"qty": qty, "entry_price": price}
        self.capital -= alloc
        
        self.trades.append({
            "time": time, "date": time.date(), "symbol": symbol, "side": "BUY",
            "price": price, "qty": qty, "net_pnl": -cost, "balance": self.capital,
            "reason": reason
        })

    def execute_sell(self, time, symbol, price, reason):
        pos = self.positions.pop(symbol)
        gross = pos['qty'] * price
        cost = gross * (self.cost_rate / 2)
        
        # PnL = (Price - Entry) * Qty - Fee -> No, fee was paid at entry too?
        # Let's align with previous audit logic:
        # Net PnL = Gross PnL - Exit Cost. (Entry Cost was PnL at Buy).
        gross_pnl = (price - pos['entry_price']) * pos['qty']
        net_pnl = gross_pnl - cost
        
        self.capital += (gross - cost)
        
        self.trades.append({
            "time": time, "date": time.date(), "symbol": symbol, "side": "SELL",
            "price": price, "qty": pos['qty'], "net_pnl": net_pnl, "gross_pnl": gross_pnl,
            "balance": self.capital, "reason": reason
        })

    def finalize(self):
        df = pd.DataFrame(self.trades)
        out_path = self.out_dir / "trades_month1_policy_v2.csv"
        df.to_csv(out_path, index=False)
        
        # Calculate Equity Curve
        final_ret = (self.capital / self.initial_capital) - 1.0
        print(f"\n[Simulation Complete]")
        print(f"Final Return: {final_ret*100:.2f}%")
        print(f"Total Trades: {len(df)}")
        print(f"Saved: {out_path}")

if __name__ == "__main__":
    sim = PolicyV2Simulator("2025-12-01", "2025-12-31")
    sim.run()
