import pandas as pd
import numpy as np
from pathlib import Path
import sys
import gc

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class PolicyV2Phase7_1_Simulator:
    def __init__(self, start_date, end_date, exp_config=None):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        
        # Default Params (Phase 7 Baseline)
        self.max_slots = 3
        # Phase 7 Fixed: self.entry_roc = -0.030
        
        # Exp Config
        self.config = exp_config if exp_config else {}
        self.use_atr_scale = self.config.get('use_atr_scale', True)
        self.atr_k = self.config.get('atr_k', 2.2) # Default 2.2
        
        self.use_confirm = self.config.get('use_confirm', False)
        self.confirm_mode = self.config.get('confirm_mode', 'A') # A: PrevHigh
        
        self.strict_switching = self.config.get('strict_switching', False)
        self.gap_th = self.config.get('gap_th', 0.2)
        
        # Exit Params (Fixed Baseline)
        self.exit_tp = 0.030 
        self.exit_sl = -0.020 
        self.cost_rate = 0.0010
        
        # Paths
        self.universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
        self.minute_dir = project_root / "GARAM_Data" / "history" / "minute"
        
        tag = f"k{self.atr_k}" if self.use_atr_scale else "fixed"
        if self.use_confirm: tag += f"_conf{self.confirm_mode}"
        if self.strict_switching: tag += "_switch"
        
        self.out_dir = project_root / "results" / "simulation" / f"5months_phase7_1_{tag}"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        self.prices = {} 
        self.capital = 10_000_000.0
        self.initial_capital = 10_000_000.0

    def run(self):
        print(f"Running Phase 7.1 (Exp: ATR={self.use_atr_scale} k={self.atr_k})")
        
        # 1. Collect Signals
        df_sig = self.collect_signals()
        
        if df_sig.empty:
            print("No signals found.")
            return
            
        print(f"Sorting {len(df_sig)} signals...")
        df_sig.sort_values(['time', 'score'], ascending=[True, False], inplace=True)
        
        self.simulate_portfolio(df_sig)

    def calculate_atr_percent(self, df, period=14):
        # ATR(14) on 5 min data?
        # User: ATR(14, 5m) / price
        # Resample to 5T
        df_5m = df.resample('5T').agg({
            'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
        }).dropna()
        
        if len(df_5m) < period + 1: return None
        
        # TR
        df_5m['prev_close'] = df_5m['close'].shift(1)
        df_5m['tr1'] = df_5m['high'] - df_5m['low']
        df_5m['tr2'] = (df_5m['high'] - df_5m['prev_close']).abs()
        df_5m['tr3'] = (df_5m['low'] - df_5m['prev_close']).abs()
        df_5m['tr'] = df_5m[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # ATR
        df_5m['atr'] = df_5m['tr'].rolling(period).mean() # Simple Mean for speed (or EMA?)
        # User said ATR(14). Usually Wilder's but simple rolling is close enough and faster.
        
        # ATR %
        df_5m['atr_pct'] = df_5m['atr'] / df_5m['close']
        
        # Map back to 1T?
        # Use reindex/ffill
        return df_5m['atr_pct']

    def collect_signals(self):
        signals = []
        df_univ = pd.read_csv(self.universe_path)
        col = next((c for c in ["Code", "code", "symbol"] if c in df_univ.columns), None)
        symbols = df_univ[col].astype(str).str.zfill(6).tolist()
        
        count = 0
        for sym in symbols:
            p = self.minute_dir / f"{sym}.csv"
            if not p.exists(): continue
            try:
                # Load
                df = pd.read_csv(p, usecols=['date', 'open', 'high', 'low', 'close', 'volume'])
                s_str = self.start_date.strftime("%Y%m%d")
                e_str = self.end_date.strftime("%Y%m%d")
                
                if df['date'].dtype != 'O': df['date'] = df['date'].astype(str)
                mask = df['date'].str[:8].between(s_str, e_str)
                df = df[mask].copy()
                if df.empty: continue
                
                df['time'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S')
                df.set_index('time', inplace=True)
                df.sort_index(inplace=True)
                
                # Indicators
                # Trend (MA60)
                daily_close = df['close'].resample('D').last().dropna()
                ma60_daily = daily_close.rolling(60).mean().shift(1)
                df['date_only'] = df.index.normalize()
                df['ma60'] = df['date_only'].map(ma60_daily)
                trend_mask = (df['close'] > df['ma60']) & (df['ma60'].notna())
                # Slope check (Phase 7.1 Feat 4 - optional, but let's stick to base Phase 7 + Exp 1)
                
                # Pullback Trigger
                df['prev_5'] = df['close'].shift(5)
                df['roc_5m'] = (df['close'] / df['prev_5']) - 1.0
                
                # Vol Accel
                df['vol_ma'] = df['volume'].rolling(11).mean()
                df['vol_accel'] = df['volume'] / df['volume'].rolling(10).mean().replace(0, 1)
                
                if self.use_atr_scale:
                    # Calc ATR %
                    atr_pct_series_5m = self.calculate_atr_percent(df)
                    if atr_pct_series_5m is None: continue
                    atr_pct_1m = atr_pct_series_5m.reindex(df.index, method='ffill')
                    df['atr_pct'] = atr_pct_1m
                    df['target_roc'] = -self.atr_k * df['atr_pct']
                    pullback_cond = df['roc_5m'] < df['target_roc']
                else:
                    pullback_cond = df['roc_5m'] < -0.030 # Fixed Phase 7
                    
                pre_entry_mask = trend_mask & pullback_cond & (df['vol_accel'] >= 1.5)
                
                # Confirm Logic (Feat 2)
                if self.use_confirm and self.confirm_mode == 'A':
                    # Signal at t if:
                    # 1. t-1 was a Trigger (Deep Pullback)
                    # 2. t breaks High(t-1)
                    # 3. t closes above High(t-1) ? Or just Intraday breakout?
                    # Vectorized: Close(t) > High(t-1).
                    # And Trigger(t-1) is True.
                    
                    df['prev_high'] = df['high'].shift(1)
                    df['trigger_shifted'] = pre_entry_mask.shift(1)
                    
                    # Confirm Condition
                    confirm_cond = (df['close'] > df['prev_high']) & (df['trigger_shifted'])
                    entry_mask = confirm_cond
                    # Note: We enter at Close of t.
                else:
                    entry_mask = pre_entry_mask

                df['ret_30m'] = df['close'].pct_change(30)
                
                # Cache needed columns
                cols = ['close', 'roc_5m']
                if self.strict_switching: cols.append('ret_30m')
                self.prices[sym] = df[cols].copy()
                
                entries = df[entry_mask]
                for t, row in entries.iterrows():
                    signals.append({
                        "time": t, "symbol": sym, "type": "ENTRY", 
                        "price": row['close'], "score": row['ret_30m']
                    })
            except: pass
            
            count += 1
            print(f"Scanned {count}/{len(symbols)}... Signals: {len(signals)}", end='\r')
            
        return pd.DataFrame(signals)

    def simulate_portfolio(self, df_sig):
        print("\nStarting Simulation...")
        signal_map = {}
        for _, row in df_sig.iterrows():
             ts = row['time']
             if ts not in signal_map: signal_map[ts] = []
             signal_map[ts].append(row)

        full_idx = pd.date_range(self.start_date, self.end_date, freq="1T")
        positions = {} 
        trades = []
        
        for t in full_idx:
            if t.hour < 9 or t.hour >= 16: continue
            if t.hour == 15 and t.minute > 30: continue
            
            # 1. Exit Logic
            for sym in list(positions.keys()):
                df = self.prices.get(sym)
                if t in df.index: p_now = df['close'].at[t]
                else: p_now = df['close'].asof(t)
                if pd.isna(p_now): continue

                entry_p = positions[sym]['entry_price']
                pnl_pct = (p_now / entry_p) - 1.0
                
                if pnl_pct < self.exit_sl:
                    self.exec_sell(t, sym, p_now, "sl", positions, trades)
                    continue
                if pnl_pct > self.exit_tp:
                    self.exec_sell(t, sym, p_now, "tp", positions, trades)
                    continue

            # 2. Entry Logic
            if t in signal_map:
                candidates = signal_map[t]
                
                # Try to Enter Top Candidates
                # If slots available -> Enter
                # If slots full -> Force Switch (Exp 3)
                
                for cand in candidates[:3]: 
                    sym_new = cand['symbol']
                    score_new = cand['score'] # ret_30m
                    price_new = cand['price']
                    
                    if sym_new in positions: continue # Already have
                    
                    if len(positions) < self.max_slots:
                        self.exec_buy(t, sym_new, price_new, "entry", positions, trades)
                    elif self.strict_switching:
                        # Full -> Check Switching Condition
                        # Find Worst Position (Lowest Score?)
                        # We need current score of holdings.
                        worst_sym = None
                        worst_score = 999.0
                        
                        for h_sym in positions:
                            # Get current score (ret_30m)
                            # Need to look up in prices
                            h_df = self.prices.get(h_sym)
                            if h_df is None: continue
                            
                            # Safe access
                            if t in h_df.index: h_score = h_df['ret_30m'].at[t]
                            else: h_score = h_df['ret_30m'].asof(t)
                            
                            if pd.isna(h_score): continue
                            
                            if h_score < worst_score:
                                worst_score = h_score
                                worst_sym = h_sym
                        
                        if worst_sym:
                            # Check Gap
                            # Gap = New - Worst
                            # Config: gap_th (e.g. 0.02 = 2%)
                            gap = score_new - worst_score
                            if gap >= self.gap_th:
                                # Execute Switch
                                # Sell Worst
                                h_df = self.prices.get(worst_sym)
                                if t in h_df.index: h_p = h_df['close'].at[t]
                                else: h_p = h_df['close'].asof(t)
                                
                                self.exec_sell(t, worst_sym, h_p, "switch_out", positions, trades)
                                # Buy New
                                self.exec_buy(t, sym_new, price_new, "switch_in", positions, trades)


            # EOD
            if t.hour == 15 and t.minute == 30:
                # Use list() to iterate over a copy of keys, as exec_sell modifies dict
                for sym in list(positions.keys()):
                     df = self.prices.get(sym)
                     if t in df.index: p_now = df['close'].at[t]
                     else: p_now = df['close'].asof(t)
                     
                     if pd.notna(p_now):
                         # Check if still in positions (safety)
                         if sym in positions:
                             self.exec_sell(t, sym, p_now, "eod", positions, trades)

        self.save_results(trades)

    def exec_buy(self, t, sym, price, reason, positions, trades):
        rem_slots = self.max_slots - len(positions)
        if rem_slots <= 0: return # Safety

        alloc = self.capital / rem_slots 
        cost = alloc * (self.cost_rate / 2)
        qty = (alloc - cost) / price
        if qty <= 0: return

        positions[sym] = {'qty': qty, 'entry_price': price, 'entry_time': t} # Update state if needed
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

    def save_results(self, trades):
        df = pd.DataFrame(trades)
        p = self.out_dir / "trades_phase7_1.csv"
        df.to_csv(p, index=False)
        ret = (self.capital / self.initial_capital) - 1.0
        print(f"\nReturn: {ret*100:.2f}% (Trades: {len(df)})")

if __name__ == "__main__":
    # Experiment 3: Strict Switching
    # Baseline + Switching (Gap 0.03 = 3%)
    config = {
        'use_atr_scale': False, 
        'use_confirm': False, 
        'strict_switching': True,
        'gap_th': 0.03 # 3% score gap required
    }
    sim = PolicyV2Phase7_1_Simulator("2025-08-01", "2025-12-31", config)
    sim.run()
