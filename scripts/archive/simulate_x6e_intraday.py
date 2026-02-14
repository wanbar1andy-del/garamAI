"""
[GARAM] X-6e Intraday Simulation: Profit Giveback & Dead Money Eviction (Advanced Rotation)
Objective: Solve "Profit Giveback" and "Dead Money" issues via strict rotation rules.

Logic (X-6e):
1. Profit Giveback: MFE >= 1.2% and PnL drops (MFE - 0.8%) -> Exit.
2. Dead Money: Held >= 12m & MFE < 0.25% & rank > 20 -> Exit.
3. TopK Rotation: Monitor Top 10.
   - Fill empty with Best.
   - If Full, Rotate Weakest Score if New - Weakest >= Delta (Smart) or New >= Hero (Override).
4. Cooldown: 30m block after exit.

Base: X-6d logic (50 Universe, etc.)
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
OUT_DIR = PROJECT_ROOT / f"logs/x6e/sim_{RUN_ID}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=[logging.FileHandler(OUT_DIR/"run.log"), logging.StreamHandler(sys.stdout)])

# Params
INITIAL_CAPITAL = 100_000_000
SLOTS = 5
FEE = 0.0003
ALLOC = 0.20

# X-6e Constants
FAIL_FAST_PNL = -0.007

# Giveback
PROFIT_GIVEBACK_MFE = 0.012
PROFIT_GIVEBACK_BACK = 0.008

# Dead Money
DEAD_MONEY_MIN = 12
DEAD_MONEY_MFE = 0.0025
DEAD_MONEY_SCORE_MIN = 0.30
DEAD_MONEY_RANK_MAX = 20

# Rotation
TOPK = 10
COOLDOWN_MIN = 30
SWITCH_DELTA = 0.6
SWITCH_LOSER_PNL = -0.003
HERO_OVERRIDE_SCORE = 3.0
MAX_SWITCHES_DAILY = 3

class X6eSimulator:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.slots = [None] * SLOTS
        self.equity_curve = []
        self.trades = []
        self.switch_count_daily = 0
        self.cur_date = None
        self.cooldown_until = {} # {ticker: timestamp}
        
        self.daily_files = None
        self.minute_data_cache = {}

    def _is_cooldown(self, tkr, t_now):
        until = self.cooldown_until.get(tkr)
        return until is not None and t_now <= until

    def _set_cooldown(self, tkr, t_now):
        self.cooldown_until[tkr] = t_now + pd.Timedelta(minutes=COOLDOWN_MIN)
        
    def load_daily_universe(self):
        logging.info("Scanning Daily Universe...")
        files = list(DATA_DIR.glob("*.csv"))
        daily_rows = []
        for f in files:
            try:
                if '329180' in f.name: continue
                df = pd.read_csv(f)
                if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
                elif 'Date' in df.columns: df.rename(columns={'Date':'date'}, inplace=True)
                
                if 'close' not in df.columns or df.empty: continue
                
                tkr = f.stem
                df['date'] = pd.to_datetime(df['date'])
                last = df.iloc[-1]
                daily_rows.append({
                    'date': df.iloc[0]['date'].date(), 
                    'ticker': tkr,
                    'path': str(f)
                })
            except: pass
        self.daily_files = pd.DataFrame(daily_rows)
        return sorted(self.daily_files['date'].unique())

    def get_minute_snapshot(self, date_obj):
        day_universe = {}
        relevant = self.daily_files[self.daily_files['date'] == date_obj]
        for _, row in relevant.iterrows():
            try:
                df = pd.read_csv(row['path'])
                if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
                elif 'Date' in df.columns: df.rename(columns={'Date':'date'}, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                
                day_df = df[df['date'].dt.date == date_obj].copy()
                if not day_df.empty:
                    day_df.set_index('date', inplace=True)
                    day_universe[row['ticker']] = day_df
            except: pass
        return day_universe

    def run(self):
        dates = self.load_daily_universe()
        
        for d in dates:
            self.cur_date = d
            self.switch_count_daily = 0
            self.cooldown_until = {} # Reset daily? Or keep? Usually reset daily for ease.
            
            day_data = self.get_minute_snapshot(d) 
            if not day_data: continue
            
            all_times = sorted(list(set().union(*[df.index for df in day_data.values()])))
            valid_times = [t for t in all_times if t.time() >= time(9,0) and t.time() <= time(15,20)]
            
            hist_c = {t: [] for t in day_data}
            hist_v = {t: [] for t in day_data}
            
            for t in valid_times:
                # 1. Update Scores & TopK
                current_cands = []
                for tkr, df in day_data.items():
                    if t in df.index:
                        row = df.loc[t]
                        c, v = float(row['close']), float(row['volume'])
                        
                        hist_c[tkr].append(c)
                        hist_v[tkr].append(v)
                        if len(hist_c[tkr]) > 20: hist_c[tkr].pop(0)
                        if len(hist_v[tkr]) > 20: hist_v[tkr].pop(0)
                        
                        if len(hist_c[tkr]) >= 5:
                            c_now = hist_c[tkr][-1]
                            c_prev5 = hist_c[tkr][-5]
                            ret5 = (c_now - c_prev5) / c_prev5
                            
                            v_now = hist_v[tkr][-1]
                            v_avg = sum(hist_v[tkr]) / len(hist_v[tkr])
                            v_spike = v_now / (v_avg + 1e-9) if v_avg > 0 else 1.0
                            v_spike = min(v_spike, 3.0)
                            
                            score = ret5 * v_spike * 100
                            current_cands.append({'ticker': tkr, 'score': score, 'px': c})
                            
                current_cands.sort(key=lambda x: x['score'], reverse=True)
                
                # TopK
                topk = current_cands[:TOPK] if current_cands else []
                
                # 2. Portfolio Management (Rule Block)
                for i in range(SLOTS):
                    pos = self.slots[i]
                    if not pos: continue

                    tkr = pos['ticker']
                    # Valid Price?
                    if tkr in day_data and t in day_data[tkr].index:
                        cur_px = float(day_data[tkr].loc[t]['close'])
                        pos['last_px'] = cur_px
                    else:
                        cur_px = pos.get('last_px', pos['entry_px'])

                    # Calc Stats
                    pnl = (cur_px - pos['entry_px']) / pos['entry_px']
                    if cur_px > pos['high_px']: pos['high_px'] = cur_px
                    mfe = (pos['high_px'] - pos['entry_px']) / pos['entry_px']
                    hold_mins = (t - pos['entry_time']).total_seconds() / 60
                    
                    # Cand Stats
                    cand_idx = next((k for k,c in enumerate(topk) if c['ticker'] == tkr), None)
                    pos_score = topk[cand_idx]['score'] if cand_idx is not None else -99.0
                    pos_rank = (cand_idx + 1) if cand_idx is not None else 999
                    
                    # (A) Profit Giveback
                    if mfe >= PROFIT_GIVEBACK_MFE:
                        if pnl <= (mfe - PROFIT_GIVEBACK_BACK):
                            self._close(i, cur_px, t, 'GIVEBACK_EXIT')
                            self._set_cooldown(tkr, t)
                            continue
                            
                    # (B) Dead Money
                    if hold_mins >= DEAD_MONEY_MIN and mfe < DEAD_MONEY_MFE:
                        if pos_score < DEAD_MONEY_SCORE_MIN or pos_rank > DEAD_MONEY_RANK_MAX:
                            self._close(i, cur_px, t, 'DEAD_MONEY_EXIT')
                            self._set_cooldown(tkr, t)
                            continue
                            
                    # Fail Fast (Hard Stop) - still valid
                    if pnl <= FAIL_FAST_PNL:
                        self._close(i, cur_px, t, 'FAIL_LOSS')
                        self._set_cooldown(tkr, t)
                        continue

                # 3. Entry & Rotation
                # Priority: Fill Empty -> Then Rotate Weakest
                
                # 3-1. Fill Empty
                for cand in topk:
                    tkr = cand['ticker']
                    if self._is_cooldown(tkr, t): continue
                    if any(p and p['ticker'] == tkr for p in self.slots): continue
                    
                    empty_idx = next((i for i,p in enumerate(self.slots) if p is None), -1)
                    if empty_idx != -1 and cand['score'] > 1.0:
                        self._open(empty_idx, tkr, cand['px'], t)
                        # Don't break? Try to fill all slots if possible
                    else:
                        break # Slots full, wait for rotation logic
                
                # 3-2. Rotation (If full and better candidate exists)
                if topk:
                    best = topk[0]
                    # If best is not held and valid
                    if not self._is_cooldown(best['ticker'], t) and not any(p and p['ticker']==best['ticker'] for p in self.slots):
                         # Find Weakest Slot (Score Base)
                         # Only if slots are effectively full or we want to upgrade
                         # Check if any slot is available first?
                         empty_idx = next((i for i,p in enumerate(self.slots) if p is None), -1)
                         if empty_idx == -1: # Full
                             weakest_idx = -1
                             weakest_score = 1e9
                             weakest_pnl = 0.0
                             
                             for i, p in enumerate(self.slots):
                                 if not p: continue
                                 tkr = p['ticker']
                                 cand_idx = next((k for k,c in enumerate(topk) if c['ticker'] == tkr), None)
                                 sc = topk[cand_idx]['score'] if cand_idx is not None else -99.0 # If not in topk, very low score
                                 
                                 # Need current PnL for check
                                 cur_pnl = (p['last_px'] - p['entry_px']) / p['entry_px']
                                 
                                 if sc < weakest_score:
                                     weakest_score = sc
                                     weakest_idx = i
                                     weakest_pnl = cur_pnl
                                     
                             if weakest_idx != -1:
                                 # Conditions
                                 hero_like = (best['score'] >= HERO_OVERRIDE_SCORE)
                                 delta = best['score'] - weakest_score
                                 cond_switch = (delta >= SWITCH_DELTA and weakest_pnl <= SWITCH_LOSER_PNL)
                                 
                                 if (hero_like or cond_switch) and self.switch_count_daily < MAX_SWITCHES_DAILY:
                                     loser = self.slots[weakest_idx]
                                     reason = 'OVERRIDE_OUT' if hero_like else 'SWITCH_OUT'
                                     self._close(weakest_idx, loser['last_px'], t, reason)
                                     self._set_cooldown(loser['ticker'], t)
                                     
                                     self._open(weakest_idx, best['ticker'], best['px'], t)
                                     if not hero_like: self.switch_count_daily += 1

            # EOD Close
            for i in range(SLOTS):
                p = self.slots[i]
                if p: self._close(i, p['last_px'], valid_times[-1], 'EOD')
            
            self._record_equity(d)

    def _open(self, idx, tkr, px, t):
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
        
        pnl_pct = ((proceeds - fee) - (p['qty'] * p['entry_px']*(1+FEE))) / (p['qty']*p['entry_px'])
        self.trades.append({
            'date': self.cur_date, 'time': t, 'ticker': p['ticker'],
            'pnl_pct': pnl_pct, 'reason': reason
        })
        self.slots[idx] = None

    def _record_equity(self, d):
        val = self.cash
        for p in self.slots:
            if p: val += p['qty'] * p['last_px']
        self.equity_curve.append({'date': d, 'equity': val})

    def report(self):
        if not self.equity_curve: return
        final_eq = self.equity_curve[-1]['equity']
        ret = (final_eq - INITIAL_CAPITAL) / INITIAL_CAPITAL
        tr_df = pd.DataFrame(self.trades)
        win_rate = (tr_df['pnl_pct'] > 0).mean() if not tr_df.empty else 0
        
        msg = f"""
        [X-6e Intraday Simulation Result]
        Return: {ret*100:.2f}% (vs X-6d: -0.32%)
        Final: {final_eq:,.0f}
        Win Rate: {win_rate*100:.1f}% ({len(tr_df)} trades)
        
        [Efficiency Stats]
        Giveback Exits: {len(tr_df[tr_df['reason']=='GIVEBACK_EXIT'])}
        Dead Money Exits: {len(tr_df[tr_df['reason']=='DEAD_MONEY_EXIT'])}
        Switches: {len(tr_df[tr_df['reason'].str.contains('SWITCH|OVERRIDE')])}
        """
        print(msg)
        (OUT_DIR/"summary.txt").write_text(msg)
        
        # Plot
        eq_df = pd.DataFrame(self.equity_curve)
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(eq_df['date'], eq_df['equity'], label='X-6e (Smart Rotation)', color='green')
        plt.title(f"X-6e Intraday Equity (Return: {ret*100:.2f}%)")
        plt.grid(True)
        
        plt.subplot(2, 1, 2)
        peak = eq_df['equity'].cummax()
        dd = (eq_df['equity'] - peak) / peak
        plt.plot(eq_df['date'], dd, label='Drawdown', color='red')
        plt.fill_between(eq_df['date'], dd, 0, color='red', alpha=0.3)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(OUT_DIR / "equity.png")

if __name__ == "__main__":
    sim = X6eSimulator()
    sim.run()
    sim.report()
