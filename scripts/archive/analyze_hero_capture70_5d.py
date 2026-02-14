"""
[GARAM] Hero 5-Day Capture 70% Analysis
Objective: Verify if 'Hero Strategy' can capture 70% of MFE (Max Favorable Excursion) within 5 days using Trailing Stop.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import sys
import logging

# Setup
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
import requests
import os

def send_telegram_report(text, image_path=None):
    token = os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('GARAM_TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print("Telegram Token missing.")
        return

    # Text
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)
    
    # Image
    if image_path and Path(image_path).exists():
        url_doc = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(image_path, 'rb') as f:
            files = {'photo': f}
            data = {'chat_id': chat_id}
            requests.post(url_doc, data=data, files=files)

# from utils.telegram_bot_v2 import send_image_to_telegram, send_message_to_telegram

# Config
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
# DATA_DIR = Path("C:/garam/garam/GARAM_Data/60day_replay_kst") # Direct path safe
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/ops/hero_capture70_5d_{RUN_ID}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(OUT_DIR / "run.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Strategy Params
INITIAL_CAPITAL = 100_000_000.0
SLOTS = 5
ALLOC_PER_SLOT = 0.20
FEE = 0.0003 # 0.03% (Buy+Sell combined estimate or One way? Usually 0.015% * 2 + Tax)
             # User said "0.03% 수준".

class HeroAnalyzer:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.slots = [None] * SLOTS
        self.equity_curve = []
        self.closed_trades = []
        self.daily_heroes = {} # {date: ticker}
        self.full_minute_data = {} 
        self.dates = []

    def load_and_prep(self):
        logging.info("Loading Data & Calculating Scores...")
        files = list(DATA_DIR.glob("*.csv"))
        files.sort()
        
        all_daily = []
        
        for i, f in enumerate(files):
            try:
                if '329180' in f.name: continue
                df = pd.read_csv(f)
                
                # Normalize
                cols = df.columns
                if 'ts' in cols: df.rename(columns={'ts':'date'}, inplace=True)
                elif 'Date' in cols: df.rename(columns={'Date':'date'}, inplace=True)
                
                # Type sanitization
                for c in ['open','high','low','close','volume']:
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
                df.dropna(subset=['close'], inplace=True)
                
                tkr = f.stem
                df['date'] = pd.to_datetime(df['date'])
                
                # Store
                self.full_minute_data[tkr] = df
                
                # Daily Agg
                df['day'] = df['date'].dt.date
                g = df.groupby('day')
                d_agg = g.agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).reset_index()
                d_agg.rename(columns={'day': 'date'}, inplace=True)
                d_agg['ticker'] = tkr
                all_daily.append(d_agg)
                
                if i % 50 == 0: print(f"Loaded {i}/{len(files)}...", end='\r')
            except: pass
            
        print("Data Load Done. concat...")
        big_df = pd.concat(all_daily, ignore_index=True)
        big_df['date'] = pd.to_datetime(big_df['date'])
        big_df.sort_values(['ticker', 'date'], inplace=True)
        
        # Scoring
        logging.info("Scoring...")
        scored_dfs = []
        for tkr, sub in big_df.groupby('ticker'):
            sub = sub.copy()
            c = sub['close'].values.astype(float)
            v = sub['volume'].values.astype(float)
            
            r5 = np.zeros_like(c)
            r20 = np.zeros_like(c)
            if len(c) > 5: r5[5:] = (c[5:] - c[:-5]) / c[:-5]
            if len(c) > 20: r20[20:] = (c[20:] - c[:-20]) / c[:-20]
            
            v_series = pd.Series(v)
            v_avg = v_series.rolling(20).mean().fillna(1).values
            v_spike = np.clip(v / (v_avg + 1e-9), 0, 3.0)
            
            erc = c * (1.0 + r20 + r5 * v_spike)
            rr = c / (erc + 1e-12)
            score = (r5 * v_spike) * (1.0 - np.abs(rr - 0.5))
            
            sub['score'] = score
            scored_dfs.append(sub)
            
        final_daily = pd.concat(scored_dfs)
        
        logging.info(f"Score Stats:\n{final_daily['score'].describe()}")
        
        # Identify Heroes
        self.dates = sorted(final_daily['date'].unique())
        for d in self.dates:
            d_fmt = d.date()
            day_stats = final_daily[final_daily['date'] == d]
            cands = day_stats[day_stats['score'] > 0]
            if not cands.empty:
                best = cands.loc[cands['score'].idxmax()]
                self.daily_heroes[d_fmt] = best['ticker'] 
        logging.info(f"Hero Days: {len(self.daily_heroes)}")

    def run(self):
        logging.info("Starting Simulation...")
        
        # Global Timeline
        # We iterate day by day
        for d in self.dates:
            d_date = d.date()
            
            # --- 1. Manage Existing Positions (Intraday) ---
            for i in range(SLOTS):
                pos = self.slots[i]
                if pos is None: continue
                
                tkr = pos['ticker']
                m_df = self.full_minute_data.get(tkr)
                if m_df is None: continue
                
                # Get Today's Bars
                day_bars = m_df[m_df['date'].dt.date == d_date]
                
                # Current Mark Price (default: prev close)
                cur_mark = pos['entry_px'] # approx
                
                if day_bars.empty:
                    pos['hold_days'] += 1
                else:
                    # Intraday Sim
                    for idx, row in day_bars.iterrows():
                        px_o, px_h, px_l, px_c = float(row['open']), float(row['high']), float(row['low']), float(row['close'])
                        cur_mark = px_c
                        
                        # Update High (MFE)
                        if px_h > pos['high_since_entry']: pos['high_since_entry'] = px_h
                        
                        mfe_pct = (pos['high_since_entry'] - pos['entry_px']) / pos['entry_px']
                        
                        # A. SL (-7%)
                        if (px_l - pos['entry_px']) / pos['entry_px'] <= -0.07:
                            # Exec
                            sl_level = pos['entry_px'] * 0.93
                            exec_px = sl_level if px_o > sl_level else px_o
                            self._close(i, exec_px, d_date, 'SL')
                            pos = None # Closed
                            break
                        
                        # B. TP1 (+7%) - Partial 50%
                        if not pos['partial_taken']:
                            tp_level = pos['entry_px'] * 1.07
                            if px_h >= tp_level:
                                exec_px = tp_level if px_o < tp_level else px_o
                                self._partial(i, exec_px, d_date)
                        
                        # C. Trailing (+10% Activation, -5% Pullback)
                        if not pos['trail_active']:
                            if mfe_pct >= 0.10:
                                pos['trail_active'] = True
                                pos['trail_high'] = px_h
                        
                        if pos['trail_active']:
                            if px_h > pos['trail_high']: pos['trail_high'] = px_h
                            
                            stop_level = pos['trail_high'] * 0.95
                            if px_l <= stop_level:
                                exec_px = stop_level if px_o > stop_level else px_o
                                self._close(i, exec_px, d_date, 'TRAIL')
                                pos = None
                                break
                    
                    # End of Day Checks
                    if pos: 
                        pos['hold_days'] += 1
                        # D. Time Stop (Hold 5 days -> sell at Close of Day 5)
                        if pos['hold_days'] >= 5:
                            exit_px = float(day_bars.iloc[-1]['close'])
                            self._close(i, exit_px, d_date, 'TIME_STOP')
                            pos = None

            # --- 2. Entry (Close) ---
            hero = self.daily_heroes.get(d_date)
            if hero:
                # Find empty slot
                empty_i = -1
                for i in range(SLOTS):
                    if self.slots[i] is None:
                        empty_i = i
                        break
                
                if empty_i >= 0:
                    # Buy
                    m_df = self.full_minute_data.get(hero)
                    if m_df is not None:
                        bars = m_df[m_df['date'].dt.date == d_date]
                        if not bars.empty:
                            entry_px = float(bars.iloc[-1]['close'])
                            self._open(empty_i, hero, entry_px, d_date)

            # --- 3. Record Equity ---
            # Cash + Value of holdings
            holdings_val = 0
            for p in self.slots:
                if p:
                    # Need current close price. 
                    # Optimization: tracked 'cur_mark' inside loop or just fetch last close
                    # For simplicity, fetch last close of 'bars' if available, else entry
                    # Simpler: We are at EOD.
                    m_df = self.full_minute_data.get(p['ticker'])
                    bars = m_df[m_df['date'].dt.date == d_date]
                    if not bars.empty:
                        px = float(bars.iloc[-1]['close'])
                        p['mark_px'] = px
                    else:
                        px = p.get('mark_px', p['entry_px'])
                    holdings_val += p['qty'] * px
            
            tot_eq = self.cash + holdings_val
            gross_exp = holdings_val
            self.equity_curve.append({
                'date': d_date, 
                'equity': tot_eq, 
                'cash': self.cash, 
                'gross': gross_exp
            })

    def _open(self, idx, tkr, px, date):
        # 1. Duplicate Check
        if any(p and p['ticker'] == tkr for p in self.slots):
            return

        # 2. Size: 20% of Current Equity, BUT capped by Available Cash
        # This prevents accidental leverage.
        cur_eq = self.equity_curve[-1]['equity'] if self.equity_curve else INITIAL_CAPITAL
        target_alloc = cur_eq * ALLOC_PER_SLOT
        
        # [CRITICAL] Cash Constraint
        alloc = min(target_alloc, max(0.0, self.cash))
        if alloc <= 0: return

        # 3. Calculate Qty with Fee
        # cost + fee <= alloc
        # cost * (1+FEE) <= alloc
        max_qty = int(alloc / (px * (1.0 + FEE)))
        if max_qty <= 0: return
        
        qty = max_qty
        cost = qty * px
        fee = cost * FEE
        
        # Double check
        if self.cash < (cost + fee):
            return 
            
        self.cash -= (cost + fee)
        
        self.slots[idx] = {
            'ticker': tkr, 'entry_px': px, 'qty': qty, 'start_qty': qty,
            'entry_date': date, 'hold_days': 0, 
            'high_since_entry': px, 'trail_active': False, 'trail_high': px,
            'partial_taken': False, 'realized_pnl': 0, 'mark_px': px
        }

    def _partial(self, idx, px, date):
        pos = self.slots[idx]
        qty_to_sell = int(pos['qty'] * 0.5)
        if qty_to_sell == 0: return

        proceeds = qty_to_sell * px
        fee = proceeds * FEE
        # Cost basis? Weighted avg.
        # Cost of sold portion
        cost = qty_to_sell * pos['entry_px']
        
        pnl = proceeds - fee - cost
        self.cash += (proceeds - fee)
        
        pos['qty'] -= qty_to_sell
        pos['realized_pnl'] += pnl
        pos['partial_taken'] = True

    def _close(self, idx, px, date, reason):
        pos = self.slots[idx]
        qty = pos['qty']
        
        proceeds = qty * px
        fee = proceeds * FEE
        cost = qty * pos['entry_px']
        pnl = proceeds - fee - cost
        
        self.cash += (proceeds - fee)
        total_pnl = pos['realized_pnl'] + pnl
        
        # Metrics
        invested = pos['start_qty'] * pos['entry_px']
        ret_pct = total_pnl / invested
        mfe_pct = (pos['high_since_entry'] - pos['entry_px']) / pos['entry_px']
        
        capture = ret_pct / mfe_pct if mfe_pct > 1e-4 else 0.0
        
        self.closed_trades.append({
            'date': date, 'ticker': pos['ticker'], 'entry': pos['entry_px'], 
            'exit': px, 'realized': ret_pct, 'mfe_5d': mfe_pct, 
            'capture': capture, 'hold_days': pos['hold_days'], 'reason': reason
        })
        self.slots[idx] = None

    def report(self):
        eq_df = pd.DataFrame(self.equity_curve)
        tr_df = pd.DataFrame(self.closed_trades)
        
        if tr_df.empty:
            print("No trades generated.")
            return

        # 1. Summary Metrics
        init = INITIAL_CAPITAL
        # ... rest of report ...
        init = INITIAL_CAPITAL
        final = eq_df.iloc[-1]['equity']
        tot_ret = (final - init) / init
        
        peak = eq_df['equity'].cummax()
        dd = (eq_df['equity'] - peak) / peak
        mdd = dd.min()
        
        wins = tr_df[tr_df['realized'] > 0]
        losses = tr_df[tr_df['realized'] <= 0]
        win_rate = len(wins) / len(tr_df) if not tr_df.empty else 0
        
        avg_win = wins['realized'].mean() if not wins.empty else 0
        avg_loss = losses['realized'].mean() if not losses.empty else 0
        
        # Capture Ratio (Winners only for correctness check?) User said "70% Capture Achievement".
        # Conditional Expectation E[Capture | Realized > 0]
        if not wins.empty:
            avg_cap_win = wins['capture'].mean()
            med_cap_win = wins['capture'].median()
        else:
            avg_cap_win = 0; med_cap_win = 0
            
        # Validation Metrics
        min_cash = eq_df['cash'].min()
        neg_cash_days = (eq_df['cash'] < 0).sum()
        eq_df['leverage'] = eq_df['gross'] / (eq_df['equity'] + 1e-9)
        max_lev = eq_df['leverage'].max()
        
        validity = "VALID"
        if neg_cash_days > 0 or max_lev > 1.05:
            validity = "INVALID (Leverage/Neg Cash detected)"
        
        summary = f"""🧪 **[Hero 70% Capture Analysis]**
ID: {RUN_ID}

**1. Performance**
* Return: {tot_ret*100:+.2f}%
* Final: {final:,.0f} KRW
* MDD: {mdd*100:.2f}%
* Win Rate: {win_rate*100:.1f}% ({len(wins)}/{len(tr_df)})

**2. Simulation Integrity**
* Status: **{validity}**
* Min Cash: {min_cash:,.0f} KRW
* Max Leverage: {max_lev:.2f}x
* Neg Cash Days: {neg_cash_days}

**2. Capture Statistics (Target 70%)**
* Avg Capture (Wins): **{avg_cap_win*100:.1f}%**
* Median Capture (Wins): **{med_cap_win*100:.1f}%**
* Verdict: {'SUCCESS' if avg_cap_win >= 0.7 else 'FAIL'}

**3. Trade Stats**
* Avg Win: {avg_win*100:.2f}%
* Avg Loss: {avg_loss*100:.2f}%
* Expectancy: {(avg_win*win_rate + avg_loss*(1-win_rate))*100:.2f}%
"""
        print(summary)
        (OUT_DIR / "summary.txt").write_text(summary, encoding='utf-8')
        tr_df.to_csv(OUT_DIR / "trades.csv", index=False)
        
        # Graphs
        # Equity
        plt.figure(figsize=(10,8))
        plt.subplot(2,1,1)
        plt.plot(eq_df['date'], eq_df['equity'], label='Equity')
        plt.title("Equity Curve")
        plt.grid(True)
        plt.subplot(2,1,2)
        plt.plot(eq_df['date'], dd, color='red', label='Drawdown')
        plt.fill_between(eq_df['date'], dd, 0, color='red', alpha=0.3)
        plt.grid(True)
        plt.savefig(OUT_DIR / "equity.png")
        
        # Capture Hist
        if not wins.empty:
            plt.figure(figsize=(8,6))
            sns.histplot(wins['capture'], kde=True, bins=20)
            plt.axvline(0.7, color='r', linestyle='--', label='Target 0.7')
            plt.title("Capture Ratio Distribution (Winning Trades)")
            plt.savefig(OUT_DIR / "capture_hist.png")
        
        # Telegram
        try:
            send_telegram_report(summary, str(OUT_DIR / "equity.png"))
            if not wins.empty:
                send_telegram_report("Capture Distribution", str(OUT_DIR / "capture_hist.png"))
        except: pass

def main():
    app = HeroAnalyzer()
    app.load_and_prep()
    app.run()
    app.report()

if __name__ == "__main__":
    main()
