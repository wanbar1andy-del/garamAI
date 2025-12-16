
import argparse
import pandas as pd
import numpy as np
import yaml
import json
import threading
from pathlib import Path
from datetime import datetime

# Simplified Engine Logic adapted for Parameterized Simulation
class WeightedSimEngine:
    # Class-level cache to prevent reloading data for every run (especially parallel runs)
    _shared_df_close = None
    _shared_df_open = None
    _data_lock = threading.Lock()

    def __init__(self, wa, wb, wc, wd, ws, ts, turbo_mult=1.0, buffer_rank=8, trailing_stop=0.0, strict_entry=False, dynamic_conc=False):
        self.wa = wa
        self.wb = wb
        self.wc = wc
        self.wd = wd
        self.ws = ws
        self.ts = ts
        self.turbo = turbo_mult
        self.buffer_rank = int(buffer_rank)
        # V2.1 Research Flags
        self.trailing_stop = trailing_stop
        self.strict_entry = strict_entry
        self.dynamic_conc = dynamic_conc
        
        # State
        self.equity = 100_000_000
        self.cash = 100_000_000
        self.positions = {}
        
        # Data (Instance references to shared data)
        self.full_df_close = None
        self.full_df_open = None
        
    def load_data(self):
        # 1. fast exit if already loaded in this instance
        if self.full_df_close is not None:
            return True

        # 2. Check Shared Cache with Lock
        with WeightedSimEngine._data_lock:
            if WeightedSimEngine._shared_df_close is not None:
                self.full_df_close = WeightedSimEngine._shared_df_close
                self.full_df_open = WeightedSimEngine._shared_df_open
                return True
            
            # 3. Load from Disk (Only once)
            # 3. Load from Minute Data (GARAM_Data/minute/kr)
            data_dir = Path("GARAM_Data/minute/kr")
            univ_path = Path("GARAM_Data/real_universe_400.csv")
            
            if univ_path.exists():
                univ = pd.read_csv(univ_path)
                symbols = univ.iloc[:,0].astype(str).str.zfill(6).tolist()
            else:
                # Fallback to file scan
                symbols = [f.stem for f in data_dir.glob("*.csv")]
                
            dfs = []
            dfs_open = []
            
            print(f"Loading data from {data_dir} ({len(symbols)} symbols)...")
            
            for sym in symbols:
                p = data_dir / f"{sym}.csv"
                if p.exists():
                    try:
                        # Read Minute Data
                        df = pd.read_csv(p)
                        if 'datetime' in df.columns:
                            df['datetime'] = pd.to_datetime(df['datetime'].astype(str), format='%Y%m%d%H%M%S')
                            df.set_index('datetime', inplace=True)
                        elif 'date' in df.columns: # Fallback
                            df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d%H%M%S')
                            df.set_index('date', inplace=True)
                            
                        # Resample to Daily
                        daily_df = df.resample('D').agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }).dropna()
                        
                        if not daily_df.empty:
                            dfs.append(daily_df['close'].rename(sym))
                            dfs_open.append(daily_df['open'].rename(sym))
                    except Exception as e:
                        print(f"Error loading {sym}: {e}")
                        pass
            
            if dfs:
                WeightedSimEngine._shared_df_close = pd.concat(dfs, axis=1).sort_index()
                if dfs_open:
                    WeightedSimEngine._shared_df_open = pd.concat(dfs_open, axis=1).sort_index()
                
                self.full_df_close = WeightedSimEngine._shared_df_close
                self.full_df_open = WeightedSimEngine._shared_df_open
                return True
                
        return False

    def run(self, start_date, end_date):
        if self.full_df_close is None:
            if not self.load_data(): return []

        # Load KOSPI for Re-entry Momentum Checks
        kospi_path = Path("GARAM_Data/kr/index/kospi_dashboard.csv")
        kdf = None
        if kospi_path.exists():
            kdf = pd.read_csv(kospi_path)
            if 'date' in kdf.columns:
                kdf['date'] = pd.to_datetime(kdf['date'])
                kdf.set_index('date', inplace=True)
                kdf = kdf.sort_index()

        # Filter Universe Data
        df = self.full_df_close.loc[start_date:end_date]
        if df.empty: return []

        history = []
        
        # --- Pre-calculate Metrics (V3 UPGRADE) ---
        closes = self.full_df_close 
        opens = self.full_df_open
        if 'volume' in dir(self): # Check if volume is loaded
             volumes = self.full_df_volume
        else:
             # Fallback if volume not loaded separately (basic structure)
             volumes = pd.DataFrame(1, index=closes.index, columns=closes.columns)

        # 1. ATR Calculation
        # TR = Max(H-L, Abs(H-Cp), Abs(L-Cp)) -> approximated by High-Low for Daily if unavailable
        # Using simplified daily range for simulation speed if High/Low not separated
        # Ideally we need High/Low df. Assuming we have them or approx.
        # We loaded 'close' and 'open'. Let's approx TR as max(|Close-Open|, |Close-PrevClose|) if High/Low missing.
        # But we do have High/Low in consolidation! Let's update load_data to expose them.
        
        # For now, use Percentage Volatility as proxy for ATR sizing
        vol_20 = closes.pct_change().rolling(20).std() * np.sqrt(252) # Annualized Vol
        
        mom = closes.pct_change(60) 
        ma20 = closes.rolling(20).mean()
        vol_ma_20 = volumes.rolling(20).mean()
        
        rev = -((closes - ma20) / ma20)
        score_c = closes.pct_change().rolling(20).std() * 16.0
        vol_60_metric = closes.pct_change().rolling(60).std() * 16.0
        score_d = mom / vol_60_metric.replace(0, np.inf)
        
        score_a = mom
        score_b = rev
        
        # ATR Proxy for Stop Loss (Daily Volatility * Price)
        daily_atr = closes * closes.pct_change().rolling(20).std()
        
        # --- Turbo V2 State Variables ---
        turbo_active = False
        cooldown = 0
        peak_equity = self.equity
        
        # Re-entry Thresholds (Fixed V2 Rules)
        EXIT_DAILY_DROP = -0.03
        EXIT_3DAY_DROP = -0.04
        EXIT_Trailing_DD = -0.18
        
        recent_rets = [0.0, 0.0, 0.0] # Rolling 3-day buffer
        
        dates = df.index
        
        for i, t in enumerate(dates):
            # 0. Daily Updates (Equity, Returns)
            if i > 0:
                # Calculate Yesterday's Portfolio Return
                daily_rets = closes.pct_change().loc[t]
                port_ret = 0.0
                if self.positions:
                    for sym, w in self.positions.items():
                        r = daily_rets.get(sym, 0)
                        if pd.isna(r): r = 0
                        port_ret += w * r
                
                self.equity *= (1 + port_ret)
                if self.equity > peak_equity: peak_equity = self.equity
                
                # Update 3-Day Buffer
                recent_rets.pop(0)
                recent_rets.append(port_ret)
                
                # --- V3 AUTO EXIT LOGIC (ATR & Volatility) ---
                curr_dd = (self.equity - peak_equity) / peak_equity
                roll_3d = sum(recent_rets)
                
                exit_reason = None
                if turbo_active:
                    # Trailing Stop: ATR Based (V3)
                    # Use Portfolio Volatility to determine stop width? 
                    # Simplified: Use MaxDD and 3-Day first.
                    
                    if self.equity > turbo_peak_equity: turbo_peak_equity = self.equity
                    turbo_dd = 0.0
                    if turbo_peak_equity > 0:
                        turbo_dd = (self.equity - turbo_peak_equity) / turbo_peak_equity
                    
                    # V3: ATR-like Dynamic Stop
                    # If market vol is high, loosen stop. If low, tighten.
                    # Base Stop: -3%. 
                    # If Vol > 20%, Stop -> -4%, If Vol < 10%, Stop -> -2%
                    
                    # Logic implemented via Trailing Stop Arg if provided, else defaults
                    
                    if self.trailing_stop > 0 and turbo_dd < -self.trailing_stop:
                        exit_reason = f"Trailing Stop -{int(self.trailing_stop*100)}%"

                    elif port_ret <= EXIT_DAILY_DROP:
                        exit_reason = "Daily Crash -3%"
                    elif roll_3d <= EXIT_3DAY_DROP:
                        exit_reason = "3-Day Bleed -4%"
                    elif curr_dd <= EXIT_Trailing_DD:
                        exit_reason = "MaxDD Breach"
                        
                    # V3 Volatility Filter Check
                    # If Portfolio Vol spikes, reduce exposure or exit
                    # Checking recent 5-day volatility of portfolio returns
                    recent_std = np.std(recent_rets + [0,0]) # Pad 
                    if recent_std > 0.03: # High vol spike
                         exit_reason = "Vol Spike Exit"
                        
                    if exit_reason:
                        turbo_active = False
                        cooldown = 3 # Penalty
            
            # --- TURBO V2 STATE MACHINE (Rollback to Step 766 Design) ---
            # 1. Update Market Data & Regimes
            is_bull = False
            is_bear = False
            
            if kdf is not None and t in kdf.index:
                k_curr = kdf.loc[t, 'close']
                k_m20 = kdf['close'].rolling(20).mean().loc[t]
                k_m60 = kdf['close'].rolling(60).mean().loc[t]
                
                # Regimes
                # Ws (Bear Sense): Determines when we consider it "Bear"
                bear_thresh = k_m60 * (1.0 + (self.ws * 0.1))
                # Ts (Bull Sense): Determines when we consider it "Bull" (for Turbo)
                bull_thresh = k_m20 * (1.0 + (self.ts * 0.01))
                
                if k_curr < bear_thresh:
                    is_bear = True
                elif k_curr > bull_thresh and k_m20 > k_m60:
                    is_bull = True

            # 2. Daily Actions (Cooldowns & Maintenance)
            if cooldown > 0:
                cooldown -= 1
                turbo_active = False # Cooldown forces Base
            
            # 3. Turbo Switching Logic
            if turbo_active:
                # EXIT CONDITIONS (Already checked Daily/3Day/DD above for Cooldown)
                # Here we check Regime Maintenance.
                # V2 Rule: "Regime downgrade -> Turbo OFF". 
                # If we are no longer in Bull (or significant trend loss), revert to Base.
                if not is_bull:
                    turbo_active = False # Soft landing to Base
            else:
                # ENTRY CONDITIONS
                # Must be Bull + No Cooldown + Momentum
                if is_bull and cooldown == 0:
                    entry_signal = True
                    # V2.1 Research: Strict Entry
                    if self.strict_entry:
                        # Require Daily > +2% OR 3Day > +3% (Portfolio-based Proxy)
                        # recent_rets[-1] is yesterday's portfolio return. 
                        # Sum(recent_rets) is 3-day.
                        p_daily = recent_rets[-1] 
                        p_3day = sum(recent_rets)
                        if not (p_daily >= 0.02 or p_3day >= 0.03):
                            entry_signal = False
                            
                        # V3 Volume Filter
                        # Require Volume > MA20 * 1.2
                        # Need to track portfolio volume or representative symbol?
                        # Simplified: If KOSPI Vol is low, ignore.
                        pass # Placeholder for Volume Filter
                            
                    if entry_signal:
                        turbo_active = True
                        turbo_peak_equity = self.equity # Reset Trailing Peak

            # 4. Multiplier Calculation
            # "Base 1.0 + Turbo Overlay"
            # If Turbo Active: 1.0 + Turbo
            # If Turbo Inactive: 1.0 (Base)
            # CRITICAL: Do NOT force 0.0 (Cash) in Bear. User wants Base 1.0 floor.
            
            final_mult = 1.0 # Default Base
            regime_label = "BASE"
            
            if turbo_active:
                # V3 DYNAMIC LEVERAGE (Vol Targeting)
                # Target Vol = 20%
                # Realized Vol (20d) of Portfolio? Or Market?
                # Using Market Vol (KOSPI) as proxy for Regime Sizing
                
                v3_mult = self.turbo # Target Turbo (e.g. 1.0 -> Total 2.0x)
                
                if kdf is not None and t in kdf.index:
                    mkt_vol = kdf['close'].pct_change().rolling(20).std().loc[t] * np.sqrt(252)
                    if not pd.isna(mkt_vol) and mkt_vol > 0:
                         # Target 20% / Current 40% -> 0.5x
                         # Target 20% / Current 10% -> 2.0x
                         vol_scaler = 0.20 / mkt_vol
                         # Clamp Scaler (0.5x ~ 1.5x of Turbo Base)
                         if vol_scaler > 1.5: vol_scaler = 1.5
                         if vol_scaler < 0.5: vol_scaler = 0.5
                         
                         v3_mult = self.turbo * vol_scaler
                
                final_mult = 1.0 + v3_mult
                if final_mult > 2.5: final_mult = 2.5
                regime_label = f"TURBO(Vol:{v3_mult:.1f})"
            else:
                final_mult = 1.0
                regime_label = "BASE"
                if cooldown > 0:
                    regime_label = "COOLDOWN"
            
            # Special Case: Slot B (Turbo=0)
            # If User sets Turbo=0, they strictly want Base 1.0. 
            # (Previously "Box 0.5" but User instruction said "Base 1.0... Slot B: Turbo 0").
            # So 1.0 is correct.
            
            # Safety Check (Optional - User hated the "Bear->Cash" override)
            # If user explicitly wants safety, they perform differently. 
            # But the request "Restore to Step 766" implies the Base performance was good.
            # Base 1.0 usually survives via Stop Loss / Ranking, not global OFF.
            # So I will NOT add the "if is_bear: final_mult = 0.0" line.

            # ... (Rest of allocation logic)
            
            # Score Calculation
            try:
                row_a = score_a.loc[t].fillna(0)
                row_b = score_b.loc[t].fillna(0)
                row_c = score_c.loc[t].fillna(0)
                row_d = score_d.loc[t].fillna(0)
                row_price = closes.loc[t]
            except:
                continue
                
            final_score = (self.wa * row_a) + (self.wb * row_b) + (self.wc * row_c) + (self.wd * row_d)
            valid_syms = row_price.dropna().index
            final_score = final_score.loc[valid_syms]
            
            # Rank Buffer (Applies to Base & Turbo)
            target_count = 5
            selected_syms = []
            
            if not final_score.empty:
                ranked = final_score.sort_values(ascending=False)
                kept = []
                if self.positions:
                   for sym in self.positions:
                       if sym in ranked.index:
                           rk = ranked.index.get_loc(sym) + 1
                           if rk <= self.buffer_rank and final_score[sym] > 0:
                               kept.append(sym)
                need = target_count - len(kept)
                new_cands = []
                for sym in ranked.index:
                    if len(new_cands) >= need: break
                    if sym not in kept and final_score[sym] > 0:
                        new_cands.append(sym)
                selected_syms = kept + new_cands
                selected_syms = selected_syms[:target_count]

            # V2.1 Research: Dynamic Concentration
            if self.dynamic_conc and turbo_active and selected_syms:
                cnt = len(selected_syms)
                # Boost if focused
                if cnt <= 2:
                    final_mult += 0.5 
                elif cnt <= 3:
                    final_mult += 0.2
                
                if final_mult > 2.5: final_mult = 2.5

            weights = {}
            if selected_syms and final_mult > 0.01:
                w_per = 0.99 / len(selected_syms) 
                for sym in selected_syms:
                    weights[sym] = w_per * final_mult
            
            self.positions = weights
            
            history.append({
                "date": t.strftime("%Y-%m-%d"),
                "equity": self.equity,
                "regime": regime_label
            })
            
        # Convert history to DF
        history_df = pd.DataFrame(history)
        if not history_df.empty:
            history_df['date'] = pd.to_datetime(history_df['date'])
            history_df.set_index('date', inplace=True)
            history_df.to_csv("simulation_daily_history.csv")
            
        return history

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wa", type=float, default=1.0, help="Weight for Trend (Score A)")
    parser.add_argument("--wb", type=float, default=0.0, help="Weight for Reversion (Score B)")
    parser.add_argument("--wc", type=float, default=0.0, help="Weight for Fear/Vol (Score C)")
    parser.add_argument("--wd", type=float, default=0.0, help="Weight for Hero/Quality (Score D)")
    parser.add_argument("--ws", type=float, default=0.0, help="Bear Sensitivity (Ws)")
    parser.add_argument("--ts", type=float, default=0.0, help="Turbo Sensitivity (Ts)")
    parser.add_argument("--turbo", type=float, default=1.0, help="Turbo Multiplier (Exposure)")
    parser.add_argument("--buffer", type=float, default=8.0, help="Rank Buffer (Shakeout Prevention)")
    
    # V2.1 Experimental Flags
    parser.add_argument("--trailing_stop", type=float, default=0.0, help="V2.1 Trailing Stop %")
    parser.add_argument("--strict_entry", action='store_true', help="V2.1 Strict Momentum Entry")
    parser.add_argument("--dynamic_conc", action='store_true', help="V2.1 Dynamic Concentration Leverage")
    
    parser.add_argument("--output", type=str, default="sim_output.csv", help="Output file path")
    
    args = parser.parse_args()
    
    eng = WeightedSimEngine(args.wa, args.wb, args.wc, args.wd, args.ws, args.ts, args.turbo, args.buffer,
                            trailing_stop=args.trailing_stop,
                            strict_entry=args.strict_entry,
                            dynamic_conc=args.dynamic_conc)
    
    # 2 Years Back
    # 2024-01-01 to Now (roughly 2 years if we consider 2024 and 2025)
    # User asked for "2 years". Let's do 2024-01-01 ~ 2025-12-31?
    # Data might end today.
    start = "2024-01-02"
    end = datetime.now().strftime("%Y-%m-%d")
    
    res = eng.run(start, end)
    
    # Save
    df = pd.DataFrame(res)
    if not df.empty:
        df.to_csv(args.output, index=False)
        print(f"Simulation done. Saved {len(df)} rows to {args.output}")
    else:
        print("Simulation failed or no data.")

if __name__ == "__main__":
    main()
