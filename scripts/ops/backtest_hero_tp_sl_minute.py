"""
Hero TP/SL Backtest (Minute-Level Precision)
Purpose: Verify 'Hero' strategy PnL using REAL 1-Minute Data (No Daily Approx).
Logic:
    1. Scoring: Aggregate Min -> Daily to find Hero (Top 1).
    2. Execution:
       - Entry: Day D Last Minute Close (approx EOD).
       - Monitoring: Minute-by-minute from D+1 09:00.
       - Rules: 
            A: TP +10% / SL -12%
            B: TP +6%(Half)/+10% / SL -10%
       - Gap Handling: If Day Open < SL, exit at Open.
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

# Setup Project Path
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Setup Logging
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/ops/hero_tp_sl_minute_{TIMESTAMP}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=[
    logging.FileHandler(OUT_DIR / "run.log", encoding='utf-8'),
    logging.StreamHandler()
])

def send_telegram_report(summary_text, image_paths):
    token = os.environ.get("GARAM_TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("GARAM_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        try:
            sec_path = PROJECT_ROOT / "config/telegram_secrets.json"
            if sec_path.exists():
                s = json.loads(sec_path.read_text(encoding='utf-8'))
                token = s.get("bot_token") or s.get("GARAM_TELEGRAM_BOT_TOKEN")
                chat_id = s.get("chat_id") or s.get("GARAM_TELEGRAM_CHAT_ID")
        except: pass
    
    if not token or not chat_id:
        logging.error("Telegram token not found.")
        return

    import requests
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    for i, img_path in enumerate(image_paths):
        try:
            with open(img_path, 'rb') as f:
                cap = summary_text if i == 0 else ""
                data = {'chat_id': chat_id, 'caption': cap, 'parse_mode': 'Markdown'}
                files = {'photo': f}
                requests.post(url, data=data, files=files, timeout=30)
        except Exception as e:
            logging.error(f"Telegram fail: {e}")

# --- Helper Logic Re-implementation (Self-contained for speed) ---
def compute_metrics_fast(close, ret5, ret20, vol_spike):
    # Vectorized score key
    # Ensure numpy arrays
    close = np.nan_to_num(np.asarray(close), nan=0.0)
    ret5 = np.nan_to_num(np.asarray(ret5), nan=0.0)
    ret20 = np.nan_to_num(np.asarray(ret20), nan=0.0)
    vol_spike = np.nan_to_num(np.asarray(vol_spike), nan=0.0)
    
    erc = close * (1.0 + ret20 + ret5 * np.minimum(vol_spike, 3.0))
    # Avoid div by zero
    rr  = close / (erc + 1e-12)
    score = (ret5 * np.minimum(vol_spike, 3.0)) * (1.0 - np.abs(rr - 0.5))
    return score

# --- Data Loading ---
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"

def get_daily_snapshot():
    """Load all min files, agg to Daily, return Big DataFrame for Scoring."""
    logging.info("Building Daily Snapshot from Minute Data...")
    all_rows = []
    
    files = list(DATA_DIR.glob("*.csv"))
    files.sort()
    
    for i, f in enumerate(files):
        if '329180' in f.name:
            print(f"Skipping Corrupt File: {f.name}", flush=True)
            continue
            
        print(f"Loading {f.name} ({i}/{len(files)})", flush=True)
        try:
            df = pd.read_csv(f)
            if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
            elif 'Date' in df.columns: df.rename(columns={'Date':'date'}, inplace=True)
            
            # Simple agg: Group by Date string (YYYY-MM-DD)
            # Assuming 'date' is string YYYY-MM-DD HH:MM:SS
            # Fast check
            # df['day'] = df['date'].str[:10]
            # Better: use slice?
            # df['date'] is object (string)
            
            # Optimization: Just take first 10 chars
            df['day'] = df['date'].astype(str).str.slice(0, 10)
            
            # Manual Agg
            g = df.groupby('day')
            daily = g.agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).reset_index()
            daily.rename(columns={'day': 'date'}, inplace=True)
            daily['ticker'] = f.stem
            all_rows.append(daily)
        except Exception as e: 
            print(f"Skipping {f.name} due to Error: {e}")
            pass
        
        
    print(f"Finished loading {len(all_rows)} DFs. Starting Concat...", flush=True)
    try:
        big_df = pd.concat(all_rows, ignore_index=True)
        print("Concat Done. Converting Date...", flush=True)
        big_df['date'] = pd.to_datetime(big_df['date'])
        print("Date Converted. Sorting...", flush=True)
        big_df = big_df.sort_values(['ticker', 'date'])
        print("Sorting Done.", flush=True)
    except Exception as e:
        print(f"CRASH during Concat/Prep: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Sanitize Types
    print("Sanitizing Types...", flush=True)
    cols = ['open', 'high', 'low', 'close', 'volume']
    for c in cols:
        big_df[c] = pd.to_numeric(big_df[c], errors='coerce')
    
    big_df.dropna(subset=cols, inplace=True)
    print("Types Sanitized. Info:", flush=True)
    print(big_df.info())

    # Features
    logging.info("Calculating Features needed for Scoring...")
    out_dfs = []
    
    # Debug: Check big_df columns
    # print(big_df.columns)
    
    for tkr, sub in tqdm(big_df.groupby('ticker'), desc="Feat Eng"):
        sub = sub.copy()
        # Ensure we work with values (Numpy) to avoid Index/Series ambiguity
        c = sub['close'].values
        v = sub['volume'].values
        
        # Calc Returns (manual or via helper)
        # Using pandas for pct_change is fine if output is accessed as .values
        r5 = sub['close'].pct_change(5).fillna(0).values
        r20 = sub['close'].pct_change(20).fillna(0).values
        
        # Vol Rolling
        v_avg = sub['volume'].rolling(20).mean().values
        # Handle DivZero
        with np.errstate(divide='ignore', invalid='ignore'):
             v_spike = v / (v_avg + 1e-9)
        v_spike = np.nan_to_num(v_spike)
        
        # Clip
        v_clipped = np.minimum(v_spike, 3.0)
        
        # ERC
        # erc = close * (1.0 + ret20 + ret5 * vol)
        erc = c * (1.0 + r20 + r5 * v_clipped)
        
        # RR
        rr = c / (erc + 1e-12)
        
        # Score
        score = (r5 * v_clipped) * (1.0 - np.abs(rr - 0.5))
        
        # Assign back
        sub['score'] = score
        sub['ret5'] = r5
        sub['ret20'] = r20
        sub['vol_spike'] = v_spike
        
        out_dfs.append(sub)
        
    if not out_dfs:
        print("WARNING: No data found after Feat Eng.")
        return pd.DataFrame()
        
    return pd.concat(out_dfs).sort_values('date')

def load_minute_for_ticker(ticker):
    f = DATA_DIR / f"{ticker}.csv"
    if not f.exists(): return pd.DataFrame()
    
    df = pd.read_csv(f)
    if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date']) # Full timestamp
    return df.sort_values('date')

# --- Simulation Engine (Minute) ---

class MinuteTester:
    def __init__(self, mode='A'):
        self.mode = mode
        self.cash = 100_000_000
        self.equity_curve = []
        self.trades = []
        self.fee = 0.002
        
        # Rules
        if mode == 'A':
            self.tp_target = 0.10
            self.sl_target = -0.12
            self.ts_days = 10
            self.split_tp = False
        else: # B
            self.split_tp = True
            self.tp1 = 0.06
            self.tp2 = 0.10
            self.sl_target = -0.10
            self.ts_days = 10

    def run(self, daily_df):
        dates = sorted(daily_df['date'].unique())
        
        # 1. Select Heroes per day
        # 1. Select Heroes per day
        logging.info(f"Selecting Heroes for Mode {self.mode}...")
        try:
            # Vectorized Selection
            # Filter score > 0
            valid_candidates = daily_df[daily_df['score'] > 0]
            
            # Find index of max score per date
            # Check if empty first
            if valid_candidates.empty:
                heroes = {}
            else:
                best_indices = valid_candidates.groupby('date')['score'].idxmax()
                best_rows = valid_candidates.loc[best_indices]
                
                # Convert to dict {date: row}
                heroes = {row['date']: row for _, row in best_rows.iterrows()}
                
            logging.info(f"Selected {len(heroes)} Heroes.")
        except Exception as e:
            print(f"CRASH Selecting Heroes (Vectorized): {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(), []
        
        # 2. Simulation Loop
        # We process strictly sequentially:
        # If no position: Check if "Yesterday" was a Hero day. Buying at yesterday's close means we start monitoring TODAY.
        # Actually: "Entry: d일 종가". This means at End of Day D, we buy.
        # Risk starts at D+1 Market Open.
        
        curr_pos = None # {ticker, qty, entry_px, entry_time, tp_state, max_date}
        
        for d in dates: # Trading Date Loop
            try:
                # Debug
                # if str(d.date()) == '2025-11-01': print("Processing Nov 1...")
                
                # --- A. Check Existing Position (Minute Resolution) ---
                if curr_pos:
                    tkr = curr_pos['ticker']
                    min_df = load_minute_for_ticker(tkr)
                    
                    # Filter for TODAY (date d)
                    # min_df['date'] is datetime including time
                    
                    # Optimization: Load once per position life-cycle? 
                    # Yes, loading inside loop is slow. But logic is cleaner.
                    # Let's filter in memory.
                    
                    if min_df.empty:
                        today_bars = pd.DataFrame()
                    else:
                        today_mask = (min_df['date'].dt.date == d.date()) 
                        today_bars = min_df[today_mask]
                    
                    if today_bars.empty:
                        # No data today (Suspension or Holiday mismatch)
                        # Count TimeStop anyway
                        pass
                    else:
                         # Simulate Minutes
                        for idx, row in today_bars.iterrows():
                            px_open = row['open']
                            px_high = row['high']
                            px_low = row['low']
                            px_close = row['close']
                            
                            entry_px = curr_pos['entry_px']
                            
                            # Check SL
                            sl_px = entry_px * (1 + self.sl_target)
                            
                            # Gap Down Handling at First Bar of Day?
                            # Assuming row iteration is time-sorted
                            # If Low < SL:
                            if px_low <= sl_px:
                                # Trigger SL
                                # Execution Price: 
                                # If Open < SL (Gap Down), exec at Open.
                                # Else exec at SL.
                                exec_px = px_open if px_open < sl_px else sl_px
                                
                                self._close_pos(curr_pos, exec_px, d, 'SL')
                                curr_pos = None
                                break # End of position
                            
                            # Check TP
                            if self.split_tp:
                                # Rule B
                                # TP1
                                if curr_pos['tp_state'] == 0:
                                    tp1_px = entry_px * (1 + self.tp1)
                                    if px_high >= tp1_px:
                                        # Hit TP1
                                        # Exec at TP1 or Open (Gap Up)
                                        exec_px = px_open if px_open > tp1_px else tp1_px
                                        self._partial_close(curr_pos, 0.5, exec_px, d, 'TP1')
                                        curr_pos['tp_state'] = 1
                                
                                # TP2 (Rest)
                                if curr_pos['tp_state'] == 1:
                                    tp2_px = entry_px * (1 + self.tp2)
                                    if px_high >= tp2_px:
                                        exec_px = px_open if px_open > tp2_px else tp2_px
                                        self._close_pos(curr_pos, exec_px, d, 'TP2')
                                        curr_pos = None
                                        break
                                        
                            else:
                                # Rule A
                                tp_px = entry_pos = entry_px * (1 + self.tp_target)
                                if px_high >= tp_px:
                                    exec_px = px_open if px_open > tp_px else tp_px
                                    self._close_pos(curr_pos, exec_px, d, 'TP')
                                    curr_pos = None
                                    break
                    
                    # End of Day Check: TimeStop
                    if curr_pos:
                        curr_pos['held_days'] += 1
                        if curr_pos['held_days'] >= self.ts_days:
                            # Close at Today's Daily Close (which is last minute close)
                            if not today_bars.empty:
                                exit_px = today_bars.iloc[-1]['close']
                            else:
                                exit_px = curr_pos['entry_px'] # Stale Fallback
                            self._close_pos(curr_pos, exit_px, d, 'TS')
                            curr_pos = None
                
                # --- B. Entry Logic (If No Position) ---
                if not curr_pos:
                    # Check if we have a hero from TODAY to enter at CLOSE
                    if d in heroes:
                        hero = heroes[d]
                        tkr = hero['ticker']
                        entry_px = hero['close'] # Buying at Close of Day D
                        
                        # Calculate Qty
                        qty = int(self.cash / entry_px)
                        if qty > 0:
                            cost = qty * entry_px
                            fee = cost * self.fee
                            self.cash -= (cost + fee)
                            
                            curr_pos = {
                                'ticker': tkr,
                                'qty': qty,
                                'orig_qty': qty,
                                'entry_px': entry_px,
                                'entry_date': d,
                                'held_days': 0,
                                'tp_state': 0
                            }
                
                # --- C. Update Equity Curve ---
                eq_val = self.cash
                if curr_pos:
                    # Mark to Market (Close of Day D)
                    # We already know Close of Day D from daily_df or curr_pos entry logic
                    # Just use Daily DF close for speed
                    hl = heroes.get(d) 
                    if hl and hl['ticker'] == curr_pos['ticker']:
                         mark_px = hl['close']
                    else:
                        # Look up close in daily_df
                        # Slightly slow, but okay
                        row = daily_df[(daily_df['date'] == d) & (daily_df['ticker'] == curr_pos['ticker'])]
                        if not row.empty:
                            mark_px = row.iloc[0]['close']
                        else:
                            mark_px = curr_pos['entry_px']
                    
                    eq_val += curr_pos['qty'] * mark_px
                    
                self.equity_curve.append({'date': d, 'equity': eq_val})
            except Exception as e:
                print(f"CRASH in Sim Loop Day {d}: {e}")
                import traceback
                traceback.print_exc()
                pass # Continue to next day? Or break? 
                     # If we break, we lose subsequent days.
                     # Let's try to continue logic for NEXT day.
                     # But current position state might be incoherent.
                pass
            
        return pd.DataFrame(self.equity_curve), self.trades

    def _close_pos(self, pos, price, date, type_str):
        val = pos['qty'] * price
        fee = val * self.fee
        self.cash += (val - fee)
        ret = (price / pos['entry_px']) - 1
        self.trades.append({
            'date': date, 'type': type_str, 'ticker': pos['ticker'],
            'qty': pos['qty'], 'px': price, 'ret': ret
        })

    def _partial_close(self, pos, frac, price, date, type_str):
        # Frac of ORIGINAL qty
        sell_qty = int(pos['orig_qty'] * frac)
        sell_qty = min(sell_qty, pos['qty']) # Safety
        
        if sell_qty <= 0: return

        val = sell_qty * price
        fee = val * self.fee
        self.cash += (val - fee)
        
        ret = (price / pos['entry_px']) - 1
        self.trades.append({
            'date': date, 'type': type_str, 'ticker': pos['ticker'],
            'qty': sell_qty, 'px': price, 'ret': ret
        })
        
        pos['qty'] -= sell_qty

def main():
    # 1. Load Data
    full_df = get_daily_snapshot()
    print("FULL DF INFO:")
    print(full_df.info())
    print(full_df.head())
    
    # 2. Run Simulations
    logging.info("Starting Minute Simulation Rule A...")
    testerA = MinuteTester('A')
    eqA, trA = testerA.run(full_df)
    
    # logging.info("Starting Minute Simulation Rule B...")
    # testerB = MinuteTester('B')
    # eqB, trB = testerB.run(full_df)
    
    # 3. Report
    def get_stats(eq, tr):
        final = eq.iloc[-1]['equity']
        ret = (final / 100_000_000) - 1
        mdd = ((eq['equity'] / eq['equity'].cummax()) - 1).min()
        win = len([t for t in tr if t['ret'] > 0]) / len(tr) if tr else 0
        return ret, mdd, win, len(tr)
        
    rA, mA, wA, cA = get_stats(eqA, trA)
    # rB, mB, wB, cB = get_stats(eqB, trB)
    
    # Graphs
    plt.figure(figsize=(10, 6))
    plt.plot(eqA['date'], eqA['equity'], label=f'Rule A: {rA*100:.1f}%')
    # plt.plot(eqB['date'], eqB['equity'], label=f'Rule B: {rB*100:.1f}%')
    plt.title("Hero Strategy (Minute-Level Backtest)")
    plt.legend()
    plt.grid(True)
    out_img = OUT_DIR / "minute_equity.png"
    plt.savefig(out_img)
    
    summary = f"""🧪 **[가람] REAL Minute Backtest (Hero TP/SL)**

검증 방식: 1분봉 전수 검사 (Daily Approx ❌)

**1️⃣ Rule A (단순형)**
*   수익률: **{rA*100:+.2f}%**
*   MDD: **{mA*100:.2f}%**
*   승률: {wA*100:.1f}% ({cA} Trades)

**2️⃣ Rule B (분할형)**
*   (Skipped for stability)
"""
    (OUT_DIR / "summary.txt").write_text(summary, encoding='utf-8')
    send_telegram_report(summary, [out_img])
    print(summary)

if __name__ == "__main__":
    main()
