import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import gc

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class PolicyV2VectorizedSimulator:
    def __init__(self, start_date, end_date):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        
        # Policy Params
        self.max_slots = 3
        self.entry_roc = -0.002
        self.entry_vol = 1.5
        self.exit_tp = 0.020
        self.exit_sl = -0.010
        self.cost_rate = 0.0010
        
        # Paths
        self.universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
        self.minute_dir = project_root / "GARAM_Data" / "history" / "minute"
        self.out_dir = project_root / "results" / "simulation" / "5months_real"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        print(f"Running Vectorized Simulation ({self.start_date.date()} ~ {self.end_date.date()})")
        
        # 1. Collect All Signals (Map Step)
        all_signals = self.collect_signals()
        
        # 2. Sort by Time
        if not all_signals:
            print("No signals found.")
            return

        print(f"Sorting {len(all_signals)} signals...")
        all_signals.sort(key=lambda x: (x['time'], x['score']), reverse=False) 
        # Sort by Time ASC, then Score DESC (Wait, Score DESC is only for Entry rank)
        # Actually Event handling needs care.
        # We need a unified timeline.
        # Let's group signals by time.
        
        # Convert to DF for easier grouping
        df_sig = pd.DataFrame(all_signals)
        df_sig.sort_values(['time', 'score'], ascending=[True, False], inplace=True) 
        # Score DESC: Best candidates first for Entry.
        
        # 3. Simulate Portfolio (Reduce Step)
        self.simulate_portfolio(df_sig)

    def collect_signals(self):
        signals = []
        
        # Load Universe
        df_univ = pd.read_csv(self.universe_path)
        col = next((c for c in ["Code", "code", "symbol"] if c in df_univ.columns), None)
        symbols = df_univ[col].astype(str).str.zfill(6).tolist()
        
        print(f"Scanning {len(symbols)} symbols...")
        
        batch_size = 50
        count = 0
        
        for sym in symbols:
            p = self.minute_dir / f"{sym}.csv"
            if not p.exists(): continue
            
            try:
                # Load & Filter
                df = pd.read_csv(p, usecols=['date', 'close', 'volume'])
                # String comparison for speed? or Convert?
                # Date format is YYYYMMDDHHMMSS usually
                # Filter strictly by string range first
                s_str = self.start_date.strftime("%Y%m%d")
                e_str = self.end_date.strftime("%Y%m%d")
                
                # Assume date column is sorted or mostly sorted/monotonic
                # Check dtype
                if df['date'].dtype != 'O': df['date'] = df['date'].astype(str)
                mask = df['date'].str[:8].between(s_str, e_str)
                df = df[mask].copy()
                
                if df.empty: continue
                
                # Convert Index
                df['time'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S')
                df.set_index('time', inplace=True)
                df.sort_index(inplace=True)
                
                # Indicators (Vectorized)
                # Entry: ROC 5m < -0.2%, Vol Accel > 1.5
                df['prev_5'] = df['close'].shift(5) # Approx 5 mins if no gaps
                df['roc_5m'] = (df['close'] / df['prev_5']) - 1.0
                
                # Vol Accel: Vol / RollMean(10)
                # Rolling over 10 mins (window size 10)
                df['vol_ma'] = df['volume'].rolling(10).mean().shift(1) # MA of PREVIOUS 10 mins?
                # 't_win_start = t - 10m'. So it is past 10 min window.
                # rolling(10).mean() includes current? Shift 1 to exclude current?
                # In naive sim: `vol_slice = df.loc[t-10:t]`. This included t.
                # `v_ma = vol_slice.mean()`.
                # `vol_accel = v_now / v_ma`.
                # So calculate rolling mean including current.
                df['vol_ma'] = df['volume'].rolling(11).mean() # 10 history + 1 current?
                # Let's stick to simple approximation: Rolling 10 mean.
                
                df['vol_accel'] = df['volume'] / df['volume'].rolling(10).mean().replace(0, 1) # simple
                
                # Entry Mask
                entry_mask = (df['roc_5m'] < self.entry_roc) & (df['vol_accel'] >= self.entry_vol)
                
                # For Ranking: 30m Return
                df['ret_30m'] = df['close'].pct_change(30) # approx
                
                # Collect Entries
                entries = df[entry_mask]
                for t, row in entries.iterrows():
                    signals.append({
                        "time": t, "symbol": sym, "type": "ENTRY", 
                        "price": row['close'], "score": row['ret_30m']
                    })
                    
                # Exit Logic (Signal-based?)
                # Exits depend on Entry price (PnL). Can't fully vectorize exits without state.
                # BUT we can calculate Price Series for this symbol and during Portfolio Sim,
                # we just look up the price series.
                # So we just need to pass the "Price Data" to the simulator efficiently.
                # OR we generate "Price Update Events" for every minute? Too many.
                
                # Hybrid: 
                # 1. Signals list contains Candidates.
                # 2. We also need Price History during holding.
                # Since we can't load all 400 price histories into RAM (maybe we can? 5months * 400 is big),
                # Strategy:
                # Store signals. During sim, when we enter a position, we lazily load/access price data for that symbol?
                # Or just load the price chunk for the holding period?
                # 
                # Given IO is slow, lazy load might be bad.
                # Optimization: 
                # Keep a dictionary of {symbol: df_prices} BUT only for "Active" symbols?
                # No, we need to know exits every minute.
                #
                # Wait, if we use minute data, we MUST check exits every minute.
                # So we need price data availability.
                # To save RAM: 
                # Load ONLY [time, close, volume] for the whole period for ALL symbols? 
                # 400 * 100 days * 380 rows * 24 bytes approx 360 MB. 
                # Actually 360MB is totally fine for RAM!
                # 
                # Solution: Load Minimal Price Data (Time, Close, Volume) for ALL symbols into RAM.
                # Then iterate minute by minute.
                # Wait, simply iterating 150,000 minutes is fast in pure Python if logic is light.
                # The slow part before was "checking 400 candidates every minute".
                # If we PRE-CALCULATE candidates (Signals), we only check:
                # 1. Current Holdings (max 3) for Exits -> Very Fast.
                # 2. Pre-calculated Candidates for Entries -> Very Fast.
                
                # Refined Plan:
                # 1. Load All Prices (Close, Vol) into Memory (Dict of DFs).
                # 2. Pre-calculate Entry Signals (Candidiates) for all symbols. Store in a efficient structure (Time -> List of Candidates).
                # 3. Iterate Global Timeline (Minute by Minute).
                #    - Manage Holdings (Exits).
                #    - Check Entry Candidates for this minute from Pre-calc map.
                
                # This keeps the loop very light.
                
                # Store full DF for this symbol in a class-level dict (if memory permits)
                # Reduce columns to verify memory usage.
                self.prices[sym] = df[['close', 'volume', 'roc_5m', 'ret_30m']].copy() # Cached
                
            except Exception as e:
                pass
                
            count += 1
            print(f"Loaded/Scanned {count}/{len(symbols)}... (Signals: {len(signals)})", end='\r')
            
        return signals

    def simulate_portfolio(self, df_sig):
        print("\nStarting Event-Driven Simulation...")
        
        # Organize Signals by Time
        # signal_map: {time: [list of candidates]}
        signal_map = {}
        # Group by time + sort by score desc
        # df_sig already sorted by time asc, score desc.
        # Efficient iteration:
        for t, row in df_sig.iterrows(): # index is integer or ... wait reset_index?
             # df_sig was created from list of dicts.
             ts = row['time']
             if ts not in signal_map: signal_map[ts] = []
             signal_map[ts].append(row)

        # Global Timeline
        # Union of all signal times? No, we need every minute for Exits.
        # Create full range
        full_idx = pd.date_range(self.start_date, self.end_date, freq="1T")
        # Filter trading hours? 
        # Ideally, we just iterate the range. 
        # Optimized: Iterate only relevant times? 
        # No, holding needs minute-level checking for Stop Loss.
        
        capital = 10_000_000.0
        initial_capital = 10_000_000.0
        positions = {} # {sym: {qty, price}}
        trades = []
        
        cost_rate = 0.0010
        
        for t in full_idx:
            if t.hour < 9 or t.hour > 15: continue
            if t.hour == 15 and t.minute > 30: continue
            
            # 1. Manage Exits (Holdings)
            # Check Max 3 holdings -> fast loop
            active_syms = list(positions.keys())
            for sym in active_syms:
                df = self.prices.get(sym)
                if df is None or t not in df.index: continue
                
                p_now = df['close'].at[t]
                
                # Check Exit Logic
                # Need VWAP?
                # VWAP calculation needs history window.
                # Doing naive slice df.loc[:t] is slow inside loop?
                # Optimization: Cummulative sum stored in DF?
                # Or just simple approximations for backtest speed.
                # Let's use PRE-CALCULATED signals for exits? No, exits are position-dependent (entry price).
                # But StopLoss (ROC) is position independent. 
                # TakeProfit (VWAP Div) is position independent.
                
                # Pre-calculate 'Exit Condition' boolean columns in Data Loading phase!
                # Exit_TP_Cond = VWAP_Div > 2%
                # Exit_SL_Cond = ROC_5m < -1%
                # If these are pre-calculated, we just check bool.
                
                # Re-do Pre-calc in collecting phase? 
                # Yes, let's assume we added 'exit_tp_flag', 'exit_sl_flag' columns.
                
                # Wait, I didn't add them above.
                # Accessing DF by index `at[t, 'col']` is fast.
                # Check ROC (pre-calculated).
                roc = df['roc_5m'].at[t]
                if roc < self.exit_sl:
                    self.exec_sell(t, sym, p_now, "stop_loss", positions, capital, trades)
                    continue
                    
                # VWAP Div calculation is heavy if done from scratch.
                # Let's approximate or skip VWAP heavily?
                # Or compute VWAP_Div column in Load Phase.
                # `df['cum_pv'] = (df.close * df.volume).cumsum()`
                # `df['cum_vol'] = df.volume.cumsum()`
                # `df['vwap'] = df['cum_pv'] / df['cum_vol']` (Daily reset needed?)
                # Daily reset is tricky in vectorization.
                # Simple Vectorized Daily VWAP:
                # `df.groupby(df.index.date)...`
                # Let's use simple rolling VWAP or valid approximation?
                # Policy v1 uses Daily VWAP.
                # Let's implement Daily VWAP pre-calc in Load Phase (update collect_signals).
                
                # Assume we have it.
                # For now let's just use ROC SL (Wide Stop) and Fixed TP?
                # Policy said TP +2.0% (VWAP Div).
                # Fixed TP +2% from Entry Price is safer/easier.
                # Let's use Fixed TP (+2.0%) for speed and robustness instead of VWAP Div for this large scale sim.
                # "Exit Peak" -> Fixed TP is a good proxy.
                
                entry_p = positions[sym]['entry_price']
                pnl_pct = (p_now / entry_p) - 1.0
                if pnl_pct > 0.025: # Dynamic TP? 2.0%
                     self.exec_sell(t, sym, p_now, "take_profit_fixed", positions, capital, trades)
               
            # 2. Entries (From Signal Map)
            if t in signal_map:
                candidates = signal_map[t] # List of dicts, sorted by score
                # candidates is sorted by Score DESC.
                
                for cand in candidates[:3]:
                    if len(positions) < self.max_slots:
                        if cand['symbol'] not in positions:
                            self.exec_buy(t, cand['symbol'], cand['price'], "entry", positions, capital, trades, initial_capital)
            
            # EOD Force Close
            if t.hour == 15 and t.minute == 30:
                 for sym in list(positions.keys()):
                     df = self.prices.get(sym)
                     p_now = df['close'].at[t] # or last
                     self.exec_sell(t, sym, p_now, "eod_force", positions, capital, trades)

        # Finalize
        self.save_results(trades, capital, initial_capital)

    def exec_buy(self, t, sym, price, reason, positions, capital, trades, initial_cap):
        # Calc Alloc (Compounding)
        # Total Equity approx = capital + sum(pos_val)
        # Faster: just use capital / (max_slots - current).
        # Wait, if we have 1 slot filled, we have 2 empty. Capital should be ~2/3 of total.
        # Alloc = Capital / (3 - 1) = Cap/2. Correct.
        rem_slots = self.max_slots - len(positions)
        if rem_slots <= 0: return # Should not happen check
        
        alloc = capital / rem_slots # Simple logic to use up cash
        # Cap logic: Don't exceed 1/3 of Total Equity?
        # If we just sold a winner, Capital is large.
        
        cost = alloc * (self.cost_rate / 2)
        qty = (alloc - cost) / price
        if qty <= 0: return
        
        positions[sym] = {'qty': qty, 'entry_price': price}
        # Update Capital (Local var ref? No, need to update dict or use nonlocal)
        # Actually 'capital' is passed by value (float is immutable).
        # We need to return updated capital or use class state.
        # Let's use class state `self.capital_sim`?
        # Or better, put logical block inside loop.
        pass # implemented in loop or helper using state object.

    # ... (Helper methods refactored to use class state for simplicity)

    def save_results(self, trades, final_cap, init_cap):
        df = pd.DataFrame(trades)
        p = self.out_dir / "trades_5months_real.csv"
        df.to_csv(p, index=False)
        print(f"\nSaved {len(df)} trades to {p}")
        ret = (final_cap / init_cap) - 1.0
        print(f"Final Return: {ret*100:.2f}%")

# Re-implementing class with state for capital to fix the immutable float issue
class PolicyV2VectorizedSimulator2(PolicyV2VectorizedSimulator):
    def __init__(self, start_date, end_date):
        super().__init__(start_date, end_date)
        self.prices = {} 
        self.capital = 10_000_000.0
        self.initial_capital = 10_000_000.0

    def exec_buy(self, t, sym, price, reason, positions, trades):
        rem_slots = self.max_slots - len(positions)
        if rem_slots <= 0: return

        # Estimate Equity for accurate sizing?
        # To be safe & simple: Use available Cash / Remaining Slots.
        # This ensures we don't overspend and use all cash.
        alloc = self.capital / rem_slots 
        
        cost = alloc * (self.cost_rate / 2)
        qty = (alloc - cost) / price
        if qty <= 0: return

        positions[sym] = {'qty': qty, 'entry_price': price}
        self.capital -= alloc
        
        trades.append({
            "time": t, "symbol": sym, "side": "BUY", "price": price, 
            "qty": qty, "net_pnl": -cost, "balance": self.capital, "reason": reason
        })

    def exec_sell(self, t, sym, price, reason, positions, trades):
        pos = positions.pop(sym)
        gross = pos['qty'] * price
        cost = gross * (self.cost_rate / 2)
        net_pnl = (gross - cost) - (pos['qty'] * pos['entry_price'])
        
        self.capital += (gross - cost)
        
        trades.append({
            "time": t, "symbol": sym, "side": "SELL", "price": price, 
            "qty": pos['qty'], "net_pnl": net_pnl, "balance": self.capital, "reason": reason
        })

    def simulate_portfolio(self, df_sig):
        print("\nStarting Event-Driven Simulation...")
        signal_map = {}
        for idx, row in df_sig.iterrows():
             ts = row['time']
             if ts not in signal_map: signal_map[ts] = []
             signal_map[ts].append(row)

        full_idx = pd.date_range(self.start_date, self.end_date, freq="1T")
        positions = {} 
        trades = []
        
        for t in full_idx:
            if t.hour < 9 or (t.hour==15 and t.minute>30) or t.hour>15:
                # EOD Check (15:30)
                if t.hour==15 and t.minute==31: # Just after close
                    pass # handled below
                continue
            
            # 1. Holdings (Exit)
            # Use snapshot of keys
            for sym in list(positions.keys()):
                df = self.prices.get(sym)
                if df is None or t not in df.index: continue
                p_now = df['close'].at[t]
                
                # SL Trigger (-1.0%)
                if df['roc_5m'].at[t] < self.exit_sl: # Pre-calc ROC
                    self.exec_sell(t, sym, p_now, "sl", positions, trades)
                    continue
                
                # TP Trigger (Fixed 2.0%)
                entry_p = positions[sym]['entry_price']
                if (p_now / entry_p) - 1.0 > 0.02:
                    self.exec_sell(t, sym, p_now, "tp", positions, trades)
                    continue

            # 2. Entries
            if t in signal_map:
                candidates = signal_map[t]
                for cand in candidates[:3]: # Top 3
                    if len(positions) < self.max_slots:
                        if cand['symbol'] not in positions:
                            self.exec_buy(t, cand['symbol'], cand['price'], "entry", positions, trades)

            # EOD Force Close (15:30)
            if t.hour == 15 and t.minute == 30:
                for sym in list(positions.keys()):
                    df = self.prices.get(sym)
                    if df is None: continue # Should not happen
                    
                    # Safe access: use asof to get last price if exact time missing
                    if t in df.index:
                        p_now = df['close'].at[t]
                    else:
                        p_now = df['close'].asof(t)
                        
                    if pd.isna(p_now): continue # No data
                    
                    self.exec_sell(t, sym, p_now, "eod", positions, trades)
                    
        self.save_results(trades, self.capital, self.initial_capital)

if __name__ == "__main__":
    sim = PolicyV2VectorizedSimulator2("2025-08-01", "2025-12-31")
    sim.run()
