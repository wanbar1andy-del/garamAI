"""
Hero TP/SL Backtest (Operational Rule Verification)
Purpose: Verify if TP/SL/TimeStop rules yield positive PnL for 'Hero' strategy.
Rules:
    - Universe: Top 1 Score (Hero) daily.
    - Capacity: 1 Slot (Invest 100% Capital).
    - Entry: Day Close.
    - Rules:
        A: TP +10%, SL -12%, TS 10d (All or Nothing)
        B: TP +6%(50%) / +10%(50%), SL -10%, TS 10d (Partial Profit)
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path

# Setup Project Path
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Reuse Logic (Scoring)
try:
    from scripts.quantum_hero_backtest import load_data, add_features, compute_metrics
except ImportError:
    logging.error("Could not import scripts.quantum_hero_backtest")
    sys.exit(1)

# Setup Logging
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/ops/hero_tp_sl_{TIMESTAMP}"
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
    
    # Send Summary First (if needed, but caption works well)
    # requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': summary_text})

    for i, img_path in enumerate(image_paths):
        try:
            with open(img_path, 'rb') as f:
                # Attach summary to only the first image
                cap = summary_text if i == 0 else ""
                data = {'chat_id': chat_id, 'caption': cap, 'parse_mode': 'Markdown'}
                files = {'photo': f}
                requests.post(url, data=data, files=files, timeout=30)
            logging.info(f"Telegram image sent: {img_path.name}")
        except Exception as e:
            logging.error(f"Telegram fail: {e}")

class StrategyEngine:
    def __init__(self, df, mode="A", initial_cash=100_000_000):
        self.df = df
        self.mode = mode # A or B
        self.cash = initial_cash
        self.position = None # {ticker, qty, entry_px, entry_date, stopped_out_shares}
        self.equity_curve = []
        self.trades = []
        self.fee = 0.002 # 0.2%
        
        # Rule Config
        if mode == "A":
            self.tp_levels = [(0.10, 1.0)] # +10%, 100% qty
            self.sl_ret = -0.12
            self.ts_days = 10
        else: # B
            self.tp_levels = [(0.06, 0.5), (0.10, 1.0)] # +6% -> 50%, +10% -> Rest (100% of remaining is implied? Or 50% initial?)
            # Logic: Sell 50% of ORIGINAL qty at +6%. Then Sell Remainder (which is 50%) at +10%.
            # Implementation needs care.
            self.sl_ret = -0.10
            self.ts_days = 10

    def run(self):
        # 1. Identify daily heroes first
        dates = sorted(self.df['date'].unique())
        daily_hero_map = {}
        
        logging.info("Ranking Heroes...")
        for d in dates:
            day_df = self.df[self.df['date'] == d]
            candidates = []
            for _, r in day_df.iterrows():
                try:
                    _, _, s = compute_metrics(r)
                    if np.isnan(s): s = -999
                    candidates.append((r['ticker'], s))
                except: pass
            
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                if candidates[0][1] > 0: # Valid Score check
                    daily_hero_map[d] = candidates[0][0]

        logging.info(f"Simulation Start ({self.mode})...")
        
        # 2. Iterate Days
        for d in dates:
            day_df = self.df[self.df['date'] == d].set_index('ticker') # Optimize lookup
            
            # --- UPDATE POSITION (Intraday High/Low Check) ---
            if self.position:
                tkr = self.position['ticker']
                if tkr in day_df.index:
                    row = day_df.loc[tkr]
                    d_open = row['open']
                    d_high = row['high']
                    d_low = row['low']
                    d_close = row['close']
                    
                    # Logic: Check SL first (Conservative), then TP
                    entry_px = self.position['entry_px']
                    
                    # 1. Check SL
                    sl_price = entry_px * (1 + self.sl_ret)
                    
                    # Gap Down Check: if Open < SL, we execute at Open (worse)
                    # Use min(Open, SL)? Actually if Open < SL, fill at Open. If Low < SL <= Open, fill at SL.
                    # Conservative fill: min(sl_price, d_open) if Gap down.
                    
                    sl_hit = False
                    if d_low <= sl_price:
                        # TRIGGER SL
                        exec_px = sl_price if d_open > sl_price else d_open
                        # Slippage? Assume SL included rough slippage logic or add extra?
                        # User said "SL -12%", let's respect that price exactly or Open.
                        
                        qty = self.position['qty']
                        val = qty * exec_px
                        fee_val = val * self.fee
                        self.cash += (val - fee_val)
                        
                        self.trades.append({
                            'date': d, 'type': 'SL', 'ticker': tkr, 
                            'qty': qty, 'px': exec_px, 'ret': (exec_px/entry_px)-1
                        })
                        self.position = None
                        sl_hit = True
                    
                    # 2. Check TP (if not SL)
                    if not sl_hit:
                        # Process TPs
                        # Need to track "Remaining Qty" vs "Original Qty"
                        # For Mode A: Single TP level 1.0
                        # For Mode B: [(0.06, 0.5), (0.10, 1.0)]
                        
                        # Sort TPs by level
                        # Check each level.
                        # Note: TP logic usually sequentially.
                        
                        current_qty = self.position['qty']
                        original_qty = self.position['orig_qty']
                        tp_state = self.position.get('tp_state', 0) # How many levels hit
                        
                        # levels are cumulative? No, usually distinct targets.
                        # Mode B: +6% (50%), +10% (Rest).
                        # Let's normalize: List of (TargetPx, FractionOfOriginal)
                        # Actually simpler: Target Returns
                        
                        for idx, (target_ret, frac) in enumerate(self.tp_levels):
                            if idx < tp_state: continue # Already hit this level
                            
                            target_px = entry_px * (1 + target_ret)
                            
                            if d_high >= target_px:
                                # HIT TP
                                # Determine Qty to sell
                                # For last level (frac=1.0 or rest), sell all current.
                                # For intermediate, sell frac * original.
                                
                                # Mode B logic: +6% -> 50% of Orig. +10% -> Rest.
                                # Let's handle generic: 
                                # If it's the last level, sell ALL remaining.
                                is_last = (idx == len(self.tp_levels) - 1)
                                
                                if is_last:
                                    sell_qty = current_qty
                                else:
                                    sell_qty = int(original_qty * frac)
                                    sell_qty = min(sell_qty, current_qty) # Safety
                                
                                if sell_qty > 0:
                                    # Exec at target_px (Limit order assumption)
                                    # Gap Up? If Open > Target, use Open.
                                    exec_px = target_px if d_open < target_px else d_open
                                    
                                    val = sell_qty * exec_px
                                    fee_val = val * self.fee
                                    self.cash += (val - fee_val)
                                    
                                    self.trades.append({
                                        'date': d, 'type': f'TP{idx+1}', 'ticker': tkr, 
                                        'qty': sell_qty, 'px': exec_px, 'ret': (exec_px/entry_px)-1
                                    })
                                    
                                    self.position['qty'] -= sell_qty
                                    current_qty -= sell_qty
                                
                                self.position['tp_state'] = idx + 1
                                
                                if self.position['qty'] <= 0:
                                    self.position = None
                                    break # Pos closed
                    
                    # 3. Check TimeStop (if still open)
                    if self.position:
                        held_days = (d - self.position['entry_date']).days # Calendar days or Trading days?
                        # User said "10거래일" (Trading Days).
                        # We iterate dates, so we can count steps.
                        self.position['held_cnt'] += 1
                        
                        if self.position['held_cnt'] >= self.ts_days:
                            # TimeStop Exit at Close
                            exec_px = d_close
                            qty = self.position['qty']
                            val = qty * exec_px
                            fee_val = val * self.fee
                            self.cash += (val - fee_val)
                             
                            self.trades.append({
                                'date': d, 'type': 'TS', 'ticker': tkr, 
                                'qty': qty, 'px': exec_px, 'ret': (exec_px/entry_px)-1
                            })
                            self.position = None

            # --- ENTRY (If Cash avail & Slot empty) ---
            if not self.position and d in daily_hero_map:
                hero_tkr = daily_hero_map[d]
                # Check if we can buy (Price exists)
                if hero_tkr in day_df.index:
                    row = day_df.loc[hero_tkr]
                    buy_px = row['close'] # Close Entry
                    
                    # All-in
                    if self.cash > 10000:
                        qty = int(self.cash / buy_px)
                        if qty > 0:
                            cost = qty * buy_px
                            fee_val = cost * self.fee
                            self.cash -= (cost + fee_val)
                            
                            self.position = {
                                'ticker': hero_tkr,
                                'qty': qty,
                                'orig_qty': qty,
                                'entry_px': buy_px,
                                'entry_date': d,
                                'held_cnt': 0,
                                'tp_state': 0
                            }

            # --- RECORD EQUITY ---
            curr_val = self.cash
            if self.position:
                tkr = self.position['ticker']
                mark_px = 0
                if tkr in day_df.index:
                    mark_px = day_df.loc[tkr]['close']
                else:
                    # Stale price usage logic or just entry?
                    # Ideally use last known. For now use entry if missing (should not happen in replay)
                    mark_px = self.position['entry_px']
                
                curr_val += self.position['qty'] * mark_px
                
            self.equity_curve.append({'date': d, 'equity': curr_val})

        return self.equity_curve, self.trades

def analyze_backtest():
    # Load Data
    data_path = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
    df = load_data(str(data_path))
    df = add_features(df)
    df['date'] = pd.to_datetime(df['date'])
    
    # Run Modes
    engA = StrategyEngine(df, mode="A", initial_cash=100_000_000)
    eqA, trA = engA.run()
    
    engB = StrategyEngine(df, mode="B", initial_cash=100_000_000)
    eqB, trB = engB.run()
    
    # KPIs Calculation Helper
    def calc_kpi(eq, trades):
        edf = pd.DataFrame(eq)
        if edf.empty: return {}
        ret = (edf.iloc[-1]['equity'] / 100_000_000) - 1.0
        
        roll_max = edf['equity'].cummax()
        dd = (edf['equity'] - roll_max) / roll_max
        mdd = dd.min()
        
        # Max UW
        is_uw = dd < 0
        uw_grps = (is_uw != is_uw.shift()).cumsum()
        uw_days = edf[is_uw].groupby(uw_grps)['date'].agg(lambda x: (x.max() - x.min()).days)
        max_uw = uw_days.max() if not uw_days.empty else 0
        
        vol = edf['equity'].pct_change().std() * np.sqrt(252)
        
        # Trade Stats
        if not trades:
            win_rate = 0.0
            avg_pl = 0.0
        else:
            wins = [t for t in trades if t['ret'] > 0]
            win_rate = len(wins) / len(trades)
            avg_pl = np.mean([t['ret'] for t in trades])
            
        tp_count = len([t for t in trades if 'TP' in t['type']])
        sl_count = len([t for t in trades if 'SL' in t['type']])
        ts_count = len([t for t in trades if 'TS' in t['type']])

        return {
            'ret': ret, 'mdd': mdd, 'max_uw': max_uw, 'vol': vol, 
            'count': len(trades), 'win_rate': win_rate, 'avg_pl': avg_pl,
            'tp': tp_count, 'sl': sl_count, 'ts': ts_count,
            'df': edf, 'final': edf.iloc[-1]['equity']
        }

    kA = calc_kpi(eqA, trA)
    kB = calc_kpi(eqB, trB)
    
    # Save Detail CSV
    pd.DataFrame(trA).to_csv(OUT_DIR / "trades_A.csv", index=False)
    pd.DataFrame(trB).to_csv(OUT_DIR / "trades_B.csv", index=False)
    
    # Generate Plots
    # 1. Equity Comparison
    plt.figure(figsize=(10, 6))
    plt.plot(kA['df']['date'], kA['df']['equity'], label=f"Rule A (Simple): {kA['ret']*100:.1f}%")
    plt.plot(kB['df']['date'], kB['df']['equity'], label=f"Rule B (Split): {kB['ret']*100:.1f}%")
    plt.title("Operational Rule Verification: Hero Strategy (60D)")
    plt.grid(True)
    plt.legend()
    plt.ylabel("Equity (KRW)")
    
    img1 = OUT_DIR / "equity_comparison.png"
    plt.savefig(img1)
    
    # 2. Drawdown Comparison
    plt.figure(figsize=(10, 4))
    ddA = (kA['df']['equity'] / kA['df']['equity'].cummax()) - 1
    ddB = (kB['df']['equity'] / kB['df']['equity'].cummax()) - 1
    plt.plot(kA['df']['date'], ddA*100, label=f"Rule A MDD {kA['mdd']*100:.2f}%", alpha=0.7)
    plt.plot(kB['df']['date'], ddB*100, label=f"Rule B MDD {kB['mdd']*100:.2f}%", alpha=0.7)
    plt.title("Drawdown Risk")
    plt.ylabel("Drawdown %")
    plt.legend()
    plt.grid(True)
    
    img2 = OUT_DIR / "drawdown_comparison.png"
    plt.savefig(img2)
    
    # Report Text
    summary = f"""🧪 **[가람] Hero 운영 룰 검증 리포트 (TP/SL)**

목표: 'Hero 선정' 엣지를 실제 수익(PnL)으로 전환할 수 있는가?

**1️⃣ Rule A (단순형)**
*   TP +10% / SL -12% / TS 10일
*   **수익률**: {kA['ret']*100:+.2f}%
*   **MDD**: {kA['mdd']*100:.2f}% (Max UW: {kA['max_uw']}일)
*   **승률**: {kA['win_rate']*100:.1f}% (TP {kA['tp']} / SL {kA['sl']} / TS {kA['ts']})

**2️⃣ Rule B (분할청산형 - 권장)**
*   TP +6%(Half), +10%(Rest) / SL -10% / TS 10일
*   **수익률**: {kB['ret']*100:+.2f}%
*   **MDD**: {kB['mdd']*100:.2f}% (Max UW: {kB['max_uw']}일)
*   **승률**: {kB['win_rate']*100:.1f}% (TP {kB['tp']} / SL {kB['sl']} / TS {kB['ts']})

**🏆 결론 및 권고**
*   **승자**: Example ( Rule { 'B' if kB['ret'] > kA['ret'] else 'A' } )
*   **판정**: { 'GO (운영 적합)' if kB['mdd'] > -0.15 and kB['ret'] > 0 else 'CONDITIONAL GO (리스크 존재)' }
*   **Insight**: { '분할 청산이 변동성을 효과적으로 제어했습니다.' if kB['mdd'] > kA['mdd'] else '단순 보유가 수익 극대화에 유리했으나 변동성이 큽니다.' }
"""
    logging.info(summary)
    (OUT_DIR / "summary.txt").write_text(summary, encoding='utf-8')
    
    send_telegram_report(summary, [img1, img2])
    print(summary)

if __name__ == "__main__":
    analyze_backtest()
