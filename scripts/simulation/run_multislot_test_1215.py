import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class MultiSlotSimulator:
    def __init__(self, target_date):
        self.target_date = target_date # "20251215"
        self.max_slots = 3
        
        self.capital = 10_000_000.0
        self.initial_capital = 10_000_000.0
        self.positions = {} # {symbol: {shares, entry_price, current_price}}
        self.trades = []
        
        # Policy V1.1 Params
        self.entry_roc = -0.002
        self.entry_vol = 1.5
        self.exit_tp = 0.020
        self.exit_sl = -0.010
        
        self.cost_rate = 0.0010
        
    def run(self):
        print(f"Running Multi-Slot Test for {self.target_date} (Max Slots: {self.max_slots})")
        
        # Load Data
        rank_path = project_root / "results" / "labels" / f"day={self.target_date}" / "hero_rank.csv"
        if not rank_path.exists():
            print("Hero Rank file not found.")
            return
            
        candidates = pd.read_csv(rank_path)['symbol'].unique()
        price_map = {}
        for sym in candidates:
             p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
             if p.exists():
                try:
                    df = pd.read_csv(p, usecols=['date', 'close', 'volume'])
                    df = df[df['date'].astype(str).str.startswith(self.target_date)].copy()
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
                    df.dropna(subset=['date', 'close'], inplace=True)
                    df.set_index('date', inplace=True)
                    price_map[str(sym).zfill(6)] = df
                except: pass
                
        # Simulate Minute by Minute
        ymd = self.target_date
        session_idx = pd.date_range(f"{ymd} 09:00", f"{ymd} 15:30", freq="1T")
        
        for t in session_idx:
            # 1. Update Prices & Check Exits
            symbols_to_remove = []
            
            # Use snapshot of keys to allow modification
            for sym, pos in list(self.positions.items()):
                df = price_map.get(sym)
                if df is None or t not in df.index: continue
                
                p_now = df['close'].at[t]
                pos['current_price'] = p_now
                
                # Check Exit (SL/TP)
                # Need Metrics
                # VWAP Div & ROC
                # Simplified for this specific test: Use same v1.1 logic
                # To be fair comparison, logic must be identical except slot count.
                
                # ... Metric Calc (Copied from v1.1) ...
                df_sofar = df.loc[:t]
                cum_vol = df_sofar['volume'].sum()
                cum_pv = (df_sofar['close'] * df_sofar['volume']).sum()
                vwap = cum_pv / cum_vol if cum_vol > 0 else p_now
                vwap_div = (p_now / vwap) - 1.0
                
                t_prev_5 = t - timedelta(minutes=5)
                # handle missing
                p_prev_5 = p_now # default
                if t_prev_5 in df.index: p_prev_5 = df['close'].at[t_prev_5]
                roc_5m = (p_now / p_prev_5) - 1.0
                
                reason = None
                if vwap_div > self.exit_tp: reason = "take_profit"
                elif roc_5m < self.exit_sl: reason = "stop_loss"
                
                if reason:
                    self.execute_sell(t, sym, p_now, reason)
                    symbols_to_remove.append(sym)
            
            # 2. Check Entries (Switching/Adding)
            # Find Candidates
            candidates_metrics = []
            
            t_prev_30 = t - timedelta(minutes=30)
            t_win_start = t - timedelta(minutes=10)
            
            for sym, df in price_map.items():
                if t not in df.index: continue
                if sym in self.positions: continue # Already holding
                
                p_now = df['close'].at[t]
                
                # Rank Metric (30m Ret)
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
                    
            # Sort by Rank (Ret 30m)
            candidates_metrics.sort(key=lambda x: x['rank_score'], reverse=True)
            
            # Try to enter Top candidates
            for cand in candidates_metrics[:3]: # Look at top few
                if len(self.positions) < self.max_slots:
                    # Logic 1: Open Slot -> Buy
                    self.execute_buy(t, cand['symbol'], cand['price'], "new_hero_entry")
                else:
                    # Logic 2: Switching (Full Slots)
                    # Check if candidate score is much better than worst holding
                    # Worst holding: Lowest rank_score?
                    # We need rank_score of holdings.
                    # This is complex to implement fully here.
                    # For this test, let's stick to "Max 3 Slots".
                    # If 3 slots full, don't switch (unless we implement forceful kick).
                    pass
    
        # Force Close End of Day
        self.force_close_all(self.target_date)
        
        # Report
        df_t = pd.DataFrame(self.trades)
        final_eq = self.capital
        for pos in self.positions.values():
            final_eq += pos['shares'] * pos['current_price']
            
        ret = (final_eq / self.initial_capital) - 1.0
        
        print("\n[Simulation Result]")
        print(f"Final Return: {ret*100:.2f}%")
        print(f"Trades Count: {len(df_t)}")
        print("Trades List:")
        print(df_t[['time', 'symbol', 'side', 'price', 'net_pnl']].to_string())
        
        # Compare with Slot-1 result
        # Load v1.1 log
        v1_path = project_root / "results" / "simulation" / "week1_v1_1" / "trades_week1_policy_v1_1.csv"
        ret_v1 = 0.0
        if v1_path.exists():
            df_v1 = pd.read_csv(v1_path)
            df_v1['date'] = pd.to_datetime(df_v1['date'])
            df_v1_day = df_v1[df_v1['date'] == self.target_date]
            pnl_v1 = df_v1_day['net_pnl'].sum()
            ret_v1 = (pnl_v1 / 10_000_000.0) # On initial capital
            
        print("\n[A/B Test Result (2025-12-15)]")
        print(f"Scenario A (Single Slot): {ret_v1*100:.2f}%")
        print(f"Scenario B (Multi-Slot):  {ret*100:.2f}%")
        print(f"Improvement:             {(ret - ret_v1)*100:.2f}%p")
        
        # Save Summary
        with open(project_root / "results" / "simulation" / "multislot_summary.txt", "w") as f:
            f.write(f"Scenario A (Single): {ret_v1*100:.2f}%\n")
            f.write(f"Scenario B (Multi):  {ret*100:.2f}%\n")
            f.write(f"Improvement:         {(ret - ret_v1)*100:.2f}%p\n")
            f.write(f"Trades (Multi):      {len(df_t)}\n")

    def execute_buy(self, time, symbol, price, reason):
        # Allocation: 1/MaxSlots of Initial Capital? Or Remaining?
        # Let's say we split capital into 3 parts: 3.3M each.
        alloc = self.initial_capital / self.max_slots
        if self.capital < alloc: alloc = self.capital # Use what's left
        
        cost = alloc * (self.cost_rate / 2)
        net_buy = alloc - cost
        qty = net_buy / price
        
        self.positions[symbol] = {"shares": qty, "entry_price": price, "current_price": price}
        self.capital -= alloc
        
        self.trades.append({
            "time": time, "symbol": symbol, "side": "BUY", "price": price, 
            "qty": qty, "net_pnl": -cost, "reason": reason
        })
        
    def execute_sell(self, time, symbol, price, reason):
        pos = self.positions.pop(symbol)
        gross = pos['shares'] * price
        cost = gross * (self.cost_rate / 2)
        net_pnl = (price - pos['entry_price']) * pos['shares'] - cost
        # Add entry cost? No, usually pnl excludes entry cost if entry cost was deducted from capital.
        # Total PnL = Net Proceeds - CostBasis.
        # Cost Basis = Entry Price * Shares (ignoring entry fee for PnL calc here for simplicity)
        # Detailed Pnl:
        # Buy: Cap -= Alloc. (Alloc = Shares*P + EntryFee). PnL = -EntryFee.
        # Sell: Cap += Shares*P - ExitFee. PnL = (Shares*P - ExitFee) - (Shares*EntryP + EntryFee).
        # To match previous script:
        # PnL recorded in trade log.
        # Let's simplify:
        
        self.capital += (gross - cost)
        self.trades.append({
            "time": time, "symbol": symbol, "side": "SELL", "price": price, 
            "qty": pos['shares'], "net_pnl": net_pnl, "reason": reason
        })

    def force_close_all(self, ymd):
        close_time = pd.Timestamp(f"{ymd} 15:35:00")
        for sym, pos in list(self.positions.items()):
            self.execute_sell(close_time, sym, pos['current_price'], "force_close")

if __name__ == "__main__":
    sim = MultiSlotSimulator("20251215")
    sim.run()
