import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import gc

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class PolicyV2Phase7Simulator:
    def __init__(self, start_date, end_date):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        
        # Policy Params (Phase 7: Quality Filter)
        self.max_slots = 3
        
        # Filter 1: Deep Pullback
        # Was -0.002 (-0.2%) -> Now -0.030 (-3.0%)
        self.entry_roc = -0.030 
        self.entry_vol = 1.0 # Slightly relaxed volume on Deep Pullback? Or keep 1.5? User said "Quality". 
        # Deep Pullback + Volume is standard "Panic Buying". Keep 1.5? Or relaxed 1.0? 
        # Let's keep 1.5 to ensure "Panic with Volume".
        # Actually, deep pullback with LOW volume is just drift. We want Sell Climax. So Volume must be high.
        self.entry_vol = 1.5 
        
        self.exit_tp = 0.050 # Increase TP for Deep Pullback? Since we buy at -3%, rebound can be +5%.
        # Let's stick to +2% or maybe +3%?
        # User didn't specify TP.
        # But Buying at -3% means we capture the V-shape. 
        # Let's start with conservative +3.0% (Better than +2.0% because entry is deeper).
        self.exit_tp = 0.030 
        
        self.exit_sl = -0.030 # Wide SL for Deep Pullback (since we enter at -3%, additional -3% is big).
        # OR Tight SL?
        # "Catching Falling Knife" -> Needs Tight SL if it fails.
        # Let's set SL -2.0%.
        self.exit_sl = -0.020 
        
        self.cost_rate = 0.0010
        
        # Paths
        self.universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
        self.minute_dir = project_root / "GARAM_Data" / "history" / "minute"
        self.out_dir = project_root / "results" / "simulation" / "5months_phase7"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        self.prices = {} 
        self.capital = 10_000_000.0
        self.initial_capital = 10_000_000.0

    def run(self):
        print(f"Running Phase 7 (Trend+DeepPullback) ({self.start_date.date()} ~ {self.end_date.date()})")
        
        # 1. Collect Signals
        df_sig = self.collect_signals()
        
        # 2. Sort & Simulate
        if df_sig.empty:
            print("No signals found.")
            return
            
        print(f"Sorting {len(df_sig)} signals...")
        df_sig.sort_values(['time', 'score'], ascending=[True, False], inplace=True)
        
        self.simulate_portfolio(df_sig)

    def collect_signals(self):
        signals = []
        df_univ = pd.read_csv(self.universe_path)
        col = next((c for c in ["Code", "code", "symbol"] if c in df_univ.columns), None)
        symbols = df_univ[col].astype(str).str.zfill(6).tolist()
        
        print(f"Scanning {len(symbols)} symbols...")
        count = 0
        
        for sym in symbols:
            p = self.minute_dir / f"{sym}.csv"
            if not p.exists(): continue
            
            try:
                # Load (Date as String first for speed filtering)
                df = pd.read_csv(p, usecols=['date', 'close', 'volume'])
                s_str = self.start_date.strftime("%Y%m%d")
                e_str = self.end_date.strftime("%Y%m%d")
                
                if df['date'].dtype != 'O': df['date'] = df['date'].astype(str)
                mask = df['date'].str[:8].between(s_str, e_str)
                df = df[mask].copy()
                
                if df.empty: continue
                
                # Convert
                df['time'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S')
                df.set_index('time', inplace=True)
                df.sort_index(inplace=True)
                
                # [Fix] Calculate MA60 BEFORE Resampling to keep "Trading Days" logic
                # (Otherwise ffill creates weekend data and distorts MA60)
                daily_close = df['close'].resample('D').last().dropna()
                ma60_daily = daily_close.rolling(60).mean()
                ma60_shifted = ma60_daily.shift(1)
                
                # [SSOT Phase 8] Time-based Logic Implementation
                # Resample to 1-min to handle missing bars correctly (Time-based ROC).
                # 1. Reindex to full minute range
                full_idx = pd.date_range(start=df.index[0], end=df.index[-1], freq='1T')
                df = df.reindex(full_idx)
                
                # 2. Fill Missing Data
                # Close: Forward Fill (Last known price)
                df['close'] = df['close'].ffill()
                # Volume: 0 for missing bars
                df['volume'] = df['volume'].fillna(0)
                
                # Map MA60 back to minute (using date_only)
                df['date_only'] = df.index.normalize()
                df['ma60'] = df['date_only'].map(ma60_shifted)
                
                # Indicators
                # 1. Trend Filter : MA60 (Daily)
                # Already calced above.
                
                # Filter 1: Close > MA60
                # Filter NaNs (first 60 days)
                
                # Filter 1: Close > MA60
                # Filter NaNs (first 60 days)
                trend_mask = (df['close'] > df['ma60']) & (df['ma60'].notna())
                
                # 2. Deep Pullback
                df['prev_5'] = df['close'].shift(5)
                df['roc_5m'] = (df['close'] / df['prev_5']) - 1.0
                
                # Vol Accel
                df['vol_ma'] = df['volume'].rolling(11).mean()
                df['vol_accel'] = df['volume'] / df['volume'].rolling(10).mean().replace(0, 1) # simple
                
                # Entry Mask
                # Trend AND Deep Pullback AND Volume
                entry_mask = trend_mask & (df['roc_5m'] < self.entry_roc) & (df['vol_accel'] >= self.entry_vol)
                
                # 30m Return (Rank)
                df['ret_30m'] = df['close'].pct_change(30)
                
                # Store Cache (Optimization: Only relevant columns)
                # We need ROC for Exit too? Yes SL is ROC based.
                # Store Cache (Optimization: Only relevant columns)
                # We need Close for Exit Checks. Volume/ROC used for Entry generation only.
                # Downcast to float32 to save memory (CRITICAL for 32-bit Python 5-month sim)
                self.prices[sym] = df[['close']].astype('float32').copy()
                
                # Collect
                entries = df[entry_mask]
                for t, row in entries.iterrows():
                    signals.append({
                        "time": t, "symbol": sym, "type": "ENTRY", 
                        "price": row['close'], "score": row['ret_30m']
                    })
                    
            except Exception: pass
            
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
            if t.hour == 15 and t.minute > 30: 
                # EOD logic done, skip
                continue
            
            # 1. Holdings (Exit)
            for sym in list(positions.keys()):
                df = self.prices.get(sym)
                if df is None: continue
                
                # Safe Access
                if t in df.index: p_now = df['close'].at[t]
                else: p_now = df['close'].asof(t)
                if pd.isna(p_now): continue

                entry_p = positions[sym]['entry_price']
                
                # SL Logic (-2.0% ?)
                # Using ROC SL (-2%) OR Fixed Price SL?
                # "Deep Pullback" usually needs Price SL from Entry.
                # If we bought at -3%, and it drops another 2% -> Out.
                pnl_pct = (p_now / entry_p) - 1.0
                if pnl_pct < self.exit_sl:
                    self.exec_sell(t, sym, p_now, "sl", positions, trades)
                    continue
                
                # TP Logic (+3.0%)
                if pnl_pct > self.exit_tp:
                    self.exec_sell(t, sym, p_now, "tp", positions, trades)
                    continue

            # 2. Entries (Max 3)
            # Only if cash available?
            # Reinvest logic.
            if t in signal_map:
                candidates = signal_map[t]
                for cand in candidates[:3]:
                    if len(positions) < self.max_slots:
                        if cand['symbol'] not in positions:
                            self.exec_buy(t, cand['symbol'], cand['price'], "entry", positions, trades)

            # EOD Force Close (15:30)
            if t.hour == 15 and t.minute == 30:
                for sym in list(positions.keys()):
                    df = self.prices.get(sym)
                    if t in df.index: p_now = df['close'].at[t]
                    else: p_now = df['close'].asof(t)
                    if pd.notna(p_now):
                         self.exec_sell(t, sym, p_now, "eod", positions, trades)

        self.save_results(trades)

    def exec_buy(self, t, sym, price, reason, positions, trades):
        rem_slots = self.max_slots - len(positions)
        if rem_slots <= 0: return

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

    def save_results(self, trades):
        df = pd.DataFrame(trades)
        p = self.out_dir / "trades_5months_phase7.csv"
        df.to_csv(p, index=False)
        print(f"\nPhase 7 Complete. Trades: {len(df)}")
        ret = (self.capital / self.initial_capital) - 1.0
        print(f"Return: {ret*100:.2f}%")

if __name__ == "__main__":
    try:
        sim = PolicyV2Phase7Simulator("2025-08-01", "2025-12-31")
        sim.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
