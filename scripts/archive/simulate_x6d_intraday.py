"""
[GARAM] X-6d Intraday Simulation: Fail-Fast & Smart Switching
Objective: Verify if explicit 'Fail-Fast' and 'Smart Switching' rules resolve "Escape Lag".

Logic:
1. Universe: Top 50 Daily Candidates (Pre-filtered by Daily Score) to save compute.
2. Intraday Score: Update Score every minute (Ret5 * VolSpike * Consistency).
3. Portfolio: 5 Slots (20% Allocation).
4. Rules (X-6d):
   - Fail-Fast: PnL < -0.7%, TimeStop (20m, <0.3% MFE).
   - Smart Switch: Delta > 0.6 & Loser < -0.3%.
   - Hero Override: Score > 3.0 -> Force Entry.

Output: 
   - logs/x6d/... (Equity, Trades, Forensic Tables).
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, time
import sys
import logging

# Setup
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Config
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/x6d/sim_{RUN_ID}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=[logging.FileHandler(OUT_DIR/"run.log"), logging.StreamHandler(sys.stdout)])

# Params
INITIAL_CAPITAL = 100_000_000
SLOTS = 5
FEE = 0.0003
ALLOC = 0.20

# X-6d Constants
FAIL_FAST_PNL = -0.007
FAIL_FAST_TIME_MIN = 20
FAIL_FAST_MFE_REQ = 0.003
SWITCH_DELTA = 0.6
SWITCH_LOSER_PNL = -0.003
HERO_OVERRIDE_SCORE = 3.0
MAX_SWITCHES_DAILY = 3

class X6dSimulator:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.slots = [None] * SLOTS
        self.equity_curve = []
        self.trades = []
        self.switch_count_daily = 0
        self.cur_date = None
        self.forensics = {'exit_lag':[], 'slot_block':[], 'switch_effect':[]}
        
        self.minute_data_cache = {} # {ticker: day_df} (swapped per day)
        
    def load_daily_universe(self):
        logging.info("Scanning Daily Universe...")
        # 1. Load Daily stats to pick top 50 candidates per day (Optimization)
        # Scan all files, calc daily score, store Top 50 tickers per Date.
        # ... (Simplified: Load all data first, agg daily, pick top)
        files = list(DATA_DIR.glob("*.csv"))
        daily_rows = []
        for f in files:
            try:
                if '329180' in f.name: continue
                df = pd.read_csv(f)
                if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
                elif 'Date' in df.columns: df.rename(columns={'Date':'date'}, inplace=True)
                
                # Validation
                if 'close' not in df.columns or df.empty: continue
                
                tkr = f.stem
                df['date'] = pd.to_datetime(df['date'])
                
                # Last close & Vol sum
                last = df.iloc[-1]
                daily_rows.append({
                    'date': df.iloc[0]['date'].date(), 
                    'ticker': tkr,
                    'close': last['close'],
                    'vol': df['volume'].sum(),
                    'path': str(f)
                })
            except: pass
            
        d_df = pd.DataFrame(daily_rows)
        # Calc simplistic Daily Score for ranking
        # We need Ret5 avg or similar. 
        # Actually, let's just use all tickers for now? 400 isn't huge for simple logic.
        # But Minute-by-Minute for 400 tickers * 380 mins * 60 days = 9M iters. heavy.
        
        # Strategy: Iterate by Day.
        # Load ALL minute data for that day into memory.
        # Step through minutes.
        self.daily_files = d_df
        return sorted(d_df['date'].unique())

    def get_minute_snapshot(self, date_obj):
        # Load minute data for ALL tickers for this specific date
        # Return dict {ticker: minute_df}
        day_universe = {}
        relevant = self.daily_files[self.daily_files['date'] == date_obj]
        
        # Optimization: Only load tickers that traded this day
        for _, row in relevant.iterrows():
            try:
                df = pd.read_csv(row['path'])
                # Norm
                if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
                elif 'Date' in df.columns: df.rename(columns={'Date':'date'}, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                
                # Filter Day
                day_df = df[df['date'].dt.date == date_obj].copy()
                if not day_df.empty:
                    day_df.set_index('date', inplace=True)
                    # Resample to 1min to align?
                    # Most are 1min.
                    day_universe[row['ticker']] = day_df
            except: pass
        return day_universe

    def calc_intraday_scores(self, minute_idx, universe_snapshot):
        # snapshot: {ticker: row (O/H/L/C/V)}
        # returns: list of sorted candidates
        cands = []
        for tkr, row in universe_snapshot.items():
            # Simplistic "Hero Score" Intraday
            # Score = (Ret5 * VolSpike)
            # We need history for Ret5.
            # Statefullness required. 
            pass 
        return []

    # REVISED ARCHITECTURE for Speed/Simplicity:
    # We cannot simulate "Universe Scoring" perfectly accurately without massive compute.
    # Proxy: Use "Daily Hero" as the primary candidate pool (Top 5 per day).
    # But X-6d is about SWITCHING.
    # Let's assume we monitor Top 10 Daily Heroes Intraday.
    
    def run(self):
        dates = self.load_daily_universe()
        
        for d in dates:
            self.cur_date = d
            self.switch_count_daily = 0
            
            # 1. Load Day's Minute Data for Universe (Top 20 Daily Candidates)
            # To simulate switching, we need alternative candidates.
            # We assume candidates are "Potential Heroes".
            
            # Pick Top 20 by Daily Volume/Ret pre-market? 
            # Or just use all? 
            # Let's load All for correctness (400 tickers is manageable per day loop).
            day_data = self.get_minute_snapshot(d) 
            if not day_data: continue
            
            # Align Timeline (09:00 - 15:30)
            # Create a localized timestamps list
            # sample_tkr = list(day_data.keys())[0]
            # times = day_data[sample_tkr].index
            
            # Union of all times
            all_times = sorted(list(set().union(*[df.index for df in day_data.values()])))
            
            # Market Hours Filter (09:00 - 15:20)
            valid_times = [t for t in all_times if t.time() >= time(9,0) and t.time() <= time(15,20)]
            
            # Tracking "History" for scoring (Rolling windows)
            # We keep rolling window of Close/Vol for all tickers.
            hist_c = {t: [] for t in day_data}
            hist_v = {t: [] for t in day_data}
            
            for t in valid_times:
                # 1. Update Market State
                current_cands = []
                
                for tkr, df in day_data.items():
                    if t in df.index:
                        row = df.loc[t]
                        c, v = float(row['close']), float(row['volume'])
                        
                        # Use list as rolling buffer (keep last 20)
                        hist_c[tkr].append(c)
                        hist_v[tkr].append(v)
                        if len(hist_c[tkr]) > 20: hist_c[tkr].pop(0)
                        if len(hist_v[tkr]) > 20: hist_v[tkr].pop(0)
                        
                        # Calc Score
                        if len(hist_c[tkr]) >= 5:
                            c_now = hist_c[tkr][-1]
                            c_prev5 = hist_c[tkr][-5]
                            ret5 = (c_now - c_prev5) / c_prev5
                            
                            # Vol Spike
                            v_now = hist_v[tkr][-1]
                            v_avg = sum(hist_v[tkr]) / len(hist_v[tkr])
                            v_spike = v_now / (v_avg + 1e-9) if v_avg > 0 else 1.0
                            v_spike = min(v_spike, 3.0)
                            
                            score = ret5 * v_spike * 100 # Scaling
                            
                            current_cands.append({
                                'ticker': tkr, 'score': score, 'px': c, 
                                'time': t
                            })
                            
                current_cands.sort(key=lambda x: x['score'], reverse=True)
                top1 = current_cands[0] if current_cands else None
                
                # 2. Manage Portfolio (Fail-Fast)
                for i in range(SLOTS):
                    pos = self.slots[i]
                    if pos:
                        # Update Mark
                        tkr = pos['ticker']
                        if tkr in day_data and t in day_data[tkr].index:
                            cur_px = float(day_data[tkr].loc[t]['close'])
                        else:
                            cur_px = pos.get('last_px', pos['entry_px'])
                        pos['last_px'] = cur_px
                            
                        # Calc PnL
                        pnl = (cur_px - pos['entry_px']) / pos['entry_px']
                        
                        # Update MFE
                        if cur_px > pos['high_px']: pos['high_px'] = cur_px
                        mfe = (pos['high_px'] - pos['entry_px']) / pos['entry_px']
                        
                        hold_mins = (t - pos['entry_time']).total_seconds() / 60
                        
                        # [RULE] Fail-Fast: Hard Loss
                        if pnl <= FAIL_FAST_PNL:
                            self._close(i, cur_px, t, 'FAIL_LOSS')
                            continue
                            
                        # [RULE] Fail-Fast: Time Efficiency
                        if hold_mins >= FAIL_FAST_TIME_MIN and mfe < FAIL_FAST_MFE_REQ:
                            self._close(i, cur_px, t, 'FAIL_TIME')
                            continue
                            
                # 3. Switching & Entry
                if top1:
                    # Check if Top1 is already held
                    is_held = any(p and p['ticker'] == top1['ticker'] for p in self.slots)
                    
                    if not is_held:
                        # A. Normal Entry (Empty Slot)
                        empty_idx = next((i for i,p in enumerate(self.slots) if p is None), -1)
                        if empty_idx != -1:
                            if top1['score'] > 1.0: # Min Enter Score
                                self._open(empty_idx, top1['ticker'], top1['px'], t)
                        else:
                            # B. Smart Switch / Override (Full Slots)
                            # Find Weakest Slot
                            # Weakest logic: Lowest Score (Logic consistency) or Lowest PnL? 
                            # User: "worst_pnl <= -0.3%" is the condition.
                            # So we look for a loser.
                            
                            loser_idx = -1
                            min_pnl = 999
                            for i, p in enumerate(self.slots):
                                if p:
                                    # Current PnL
                                    cur_pnl = (p['last_px'] - p['entry_px']) / p['entry_px']
                                    if cur_pnl < min_pnl:
                                        min_pnl = cur_pnl
                                        loser_idx = i
                            
                            if loser_idx != -1:
                                loser = self.slots[loser_idx]
                                # Get Loser Current Score for Delta calc
                                # Need to match loser ticker in current_cands
                                loser_cand = next((c for c in current_cands if c['ticker'] == loser['ticker']), None)
                                loser_score = loser_cand['score'] if loser_cand else 0.0
                                
                                delta = top1['score'] - loser_score
                                
                                # Condition 1: Smart Switch
                                cond_switch = (delta >= SWITCH_DELTA) and (min_pnl <= SWITCH_LOSER_PNL) and (self.switch_count_daily < MAX_SWITCHES_DAILY)
                                
                                # Condition 2: Hero Override
                                cond_override = (top1['score'] >= HERO_OVERRIDE_SCORE)
                                
                                if cond_override or cond_switch:
                                    reason = 'OVERRIDE' if cond_override else 'SWITCH'
                                    self._close(loser_idx, loser['last_px'], t, f'{reason}_OUT')
                                    self._open(loser_idx, top1['ticker'], top1['px'], t)
                                    if not cond_override: self.switch_count_daily += 1
                                    
            # End of Day Cleanup (Close All)
            for i in range(SLOTS):
                p = self.slots[i]
                if p:
                    self._close(i, p['last_px'], valid_times[-1], 'EOD')
                    
            # Record Daily Equity
            self._record_equity(d)

    def _open(self, idx, tkr, px, t):
        # Strict Cash/Dup Check
        if any(p and p['ticker'] == tkr for p in self.slots): return
        
        cur_eq = self.equity_curve[-1]['equity'] if self.equity_curve else INITIAL_CAPITAL
        alloc = min(cur_eq * ALLOC, max(0, self.cash))
        if alloc <= 0: return 
        
        qty = int(alloc / (px * (1+FEE)))
        if qty <= 0: return
        
        cost = qty * px
        fee = cost * FEE
        if self.cash < cost+fee: return
        
        self.cash -= (cost+fee)
        self.slots[idx] = {
            'ticker': tkr, 'entry_px': px, 'entry_time': t,
            'qty': qty, 'high_px': px, 'last_px': px
        }

    def _close(self, idx, px, t, reason):
        p = self.slots[idx]
        proceeds = p['qty'] * px
        fee = proceeds * FEE
        self.cash += (proceeds - fee)
        
        pnl = (proceeds - fee) - (p['qty'] * p['entry_px'] * (1+FEE)) # Net PnL amount
        pnl_pct = pnl / (p['qty'] * p['entry_px']) # Approx pct
        
        self.trades.append({
            'date': self.cur_date, 'time': t, 'ticker': p['ticker'],
            'pnl_pct': pnl_pct, 'reason': reason, 'hold_min': (t - p['entry_time']).total_seconds()/60
        })
        self.slots[idx] = None

    def _record_equity(self, d):
        val = self.cash
        for p in self.slots:
            if p: val += p['qty'] * p['last_px']
        
        self.equity_curve.append({'date': d, 'equity': val})

    def report(self):
        # Summary
        if not self.equity_curve: return
        
        final_eq = self.equity_curve[-1]['equity']
        ret = (final_eq - INITIAL_CAPITAL) / INITIAL_CAPITAL
        
        tr_df = pd.DataFrame(self.trades)
        win_rate = (tr_df['pnl_pct'] > 0).mean() if not tr_df.empty else 0
        
        msg = f"""
        [X-6d Intraday Simulation Result]
        Return: {ret*100:.2f}%
        Final: {final_eq:,.0f}
        Win Rate: {win_rate*100:.1f}% ({len(tr_df)} trades)
        
        [Fail-Fast Stats]
        Hard Loss Exits: {len(tr_df[tr_df['reason']=='FAIL_LOSS'])}
        Time Stop Exits: {len(tr_df[tr_df['reason']=='FAIL_TIME'])}
        
        [Switching Stats]
        Switches: {len(tr_df[tr_df['reason'].str.contains('SWITCH|OVERRIDE')])}
        """
        print(msg)
        (OUT_DIR/"summary.txt").write_text(msg)
        tr_df.to_csv(OUT_DIR/"trades.csv")
        
        # Plotting
        if self.equity_curve:
            eq_df = pd.DataFrame(self.equity_curve)
            plt.figure(figsize=(12, 6))
            
            # Main Equity
            plt.subplot(2, 1, 1)
            plt.plot(eq_df['date'], eq_df['equity'], label='X-6d (Fail-Fast)', color='blue')
            plt.title(f"X-6d Intraday Equity (Return: {ret*100:.2f}%)")
            plt.grid(True)
            plt.legend()
            
            # Drawdown
            plt.subplot(2, 1, 2)
            peak = eq_df['equity'].cummax()
            dd = (eq_df['equity'] - peak) / peak
            plt.plot(eq_df['date'], dd, label='Drawdown', color='red')
            plt.fill_between(eq_df['date'], dd, 0, color='red', alpha=0.3)
            plt.grid(True)
            
            plt.tight_layout()
            plt.savefig(OUT_DIR / "equity.png")
            print(f"Graph saved to {OUT_DIR / 'equity.png'}")
        
if __name__ == "__main__":
    sim = X6dSimulator()
    sim.run()
    sim.report()
