"""
Backtest Portfolio 3M (Read-Only)
Running Quantum Hero Strategy with 5-Slot Portfolio (De-Molbbang)
Historical data (2025-10-01 ~ Now).
"""
import os
import sys
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Import logic
from scripts.quantum_hero_backtest import load_data, add_features, compute_metrics, Q1Config

# Setup Logging
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/ops/backtest_portfolio_3m_{TIMESTAMP}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=[
    logging.FileHandler(OUT_DIR / "run.log", encoding='utf-8'),
    logging.StreamHandler()
])

def send_telegram_report(summary_text, image_path):
    token = os.environ.get("GARAM_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("GARAM_TELEGRAM_CHAT_ID")
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
    try:
        with open(image_path, 'rb') as f:
            data = {'chat_id': chat_id, 'caption': summary_text, 'parse_mode': 'Markdown'}
            files = {'photo': f}
            requests.post(url, data=data, files=files, timeout=30)
        logging.info("Telegram report sent.")
    except Exception as e:
        logging.error(f"Telegram fail: {e}")

class PortfolioEngine:
    def __init__(self, df, slots=5, initial_capital=100_000_000, entry_q=0.7):
        self.df = df
        self.slots = slots
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {} # ticker -> {shares, mark_px}
        self.equity_curve = []
        self.trades = []
        self.entry_threshold = 0.0
        
        # Calibrate Threshold (Simple Daily Max Q)
        logging.info("Calibrating Threshold...")
        tmp = df.copy()
        # Vectorized scoring (simplified for calibration)
        # Re-using scalar compute_metrics in loop for simplicity in run, 
        # but for threshold we need vector or loop. 
        # Let's do a quick grouping.   
        max_scores = []
        for date, g in tmp.groupby('date'):
            scores = []
            for _, r in g.iterrows():
                _, _, s = compute_metrics(r)
                scores.append(s)
            if scores: max_scores.append(max(scores))
        
        self.entry_threshold = pd.Series(max_scores).quantile(entry_q)
        logging.info(f"Entry Threshold (Q{entry_q}): {self.entry_threshold:.4f}")

    def run(self):
        dates = sorted(self.df["date"].unique())
        dates = [d for d in dates if d >= pd.Timestamp("2025-10-01")]
        
        logging.info(f"Running Portfolio Simulation ({len(dates)} days, {self.slots} slots)...")
        
        fee = 0.002 # 0.2%
        
        for d in dates:
            day_data = self.df[self.df["date"] == d].copy()
            
            # 1. Update Portfolio Value (MTM)
            current_equity = self.cash
            holdings_value = 0.0
            
            # Update Prices
            for tkr in list(self.positions.keys()):
                row = day_data[day_data['ticker'] == tkr]
                if not row.empty:
                    px = float(row.iloc[0]['close'])
                    self.positions[tkr]['mark_px'] = px
                val = self.positions[tkr]['shares'] * self.positions[tkr]['mark_px']
                holdings_value += val
                
            current_equity += holdings_value
            self.equity_curve.append({'date': d, 'equity': current_equity})
            
            # 2. Ranking & Selection
            candidates = []
            for _, r in day_data.iterrows():
                _, _, score = compute_metrics(r)
                if score > 0:
                    candidates.append({'ticker': r['ticker'], 'price': r['close'], 'score': score})
            
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Top N are target portfolio
            # Simple Logic: 
            # - Sell if not in Top N (or score drops significantly? Let's stay rigid for now: Top N only)
            # - Use Top `slots` candidates that meet threshold.
            
            valid_candidates = [c for c in candidates if c['score'] >= self.entry_threshold]
            targets = valid_candidates[:self.slots] # Max 5 targets
            target_tickers = set(t['ticker'] for t in targets)
            
            # 3. Sell (Exit)
            # Sell any position NOT in target list
            # (Strict Rebalance Strategy)
            
            for tkr in list(self.positions.keys()):
                if tkr not in target_tickers:
                    # SELL
                    info = self.positions[tkr]
                    px = info['mark_px'] # Assumes close execution
                    amt = info['shares'] * px
                    proceeds = amt * (1 - fee)
                    self.cash += proceeds
                    del self.positions[tkr]
                    self.trades.append({'date': d, 'type': 'SELL', 'ticker': tkr, 'px': px})
            
            # 4. Buy (Entry)
            # Fill empty slots
            
            current_slots = len(self.positions)
            free_slots = self.slots - current_slots
            
            if free_slots > 0:
                # Calculate capital per slot (Dynamic or Fixed?)
                # Standard: Equity / Slots
                target_size = current_equity / self.slots
                
                for t in targets:
                    if t['ticker'] not in self.positions:
                        if self.cash < target_size * 0.5: # Insufficient cash
                            break
                        
                        # BUY
                        cost = target_size
                        if cost > self.cash: cost = self.cash # Cap at cash
                        
                        px = t['price']
                        shares = int(cost / px)
                        if shares > 0:
                            actual_cost = shares * px
                            self.cash -= actual_cost * (1 + fee) # Fee on entry?? usually yes or no. Let's assume on principal.
                            # wait, strict formula: cost = shares * px * (1+fee).
                            # shares = cash / (px * 1.002)
                            
                            self.positions[t['ticker']] = {'shares': shares, 'mark_px': px}
                            self.trades.append({'date': d, 'type': 'BUY', 'ticker': t['ticker'], 'px': px})
                            
        return self.equity_curve, self.trades

def run():
    # Data Path
    data_path = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
    if not data_path.exists():
        logging.error("Data missing.")
        return

    # Load
    df = load_data(str(data_path))
    df = add_features(df)
    
    # Run Portfolio Engine
    sim = PortfolioEngine(df, slots=5, initial_capital=100_000_000, entry_q=0.7)
    eq_curve, trades = sim.run()
    
    # Stats
    final_equity = eq_curve[-1]['equity']
    total_ret = (final_equity / 100_000_000) - 1.0
    
    # MDD
    peak = -9e9
    mdd = 0.0
    vals = [x['equity'] for x in eq_curve]
    for v in vals:
        if v > peak: peak = v
        dd = (v - peak) / peak
        if dd < mdd: mdd = dd
        
    summary = f"""📊 **[가람] 포트폴리오(5분할) 백테스트**

- "몰빵(All-in) 정책 삭제" 적용 결과
- 기간: 2025-10-01 ~ Now
- 설정: 5개 종목 분산 20% (Equal Weight)
- 초기자본: 1억 원
- 최종자본: {final_equity:,.0f} 원
- 총수익률: {total_ret*100:+.2f}%
- MDD: {mdd*100:.2f}%
- 트레이드: {len(trades)}회
"""
    logging.info(summary)
    (OUT_DIR / "summary.txt").write_text(summary, encoding='utf-8')
    
    # Plot
    df_eq = pd.DataFrame(eq_curve)
    df_eq['date'] = pd.to_datetime(df_eq['date'])
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
    ax1.plot(df_eq['date'], df_eq['equity'], label='Equity', color='green')
    ax1.set_title(f"5-Slot Portfolio (Net Return {total_ret*100:.1f}%)")
    ax1.grid(True)
    ax1.legend()
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # Drawdown
    roll_max = df_eq['equity'].cummax()
    drawdown = (df_eq['equity'] - roll_max) / roll_max * 100
    ax2.fill_between(df_eq['date'], drawdown, 0, color='red', alpha=0.3)
    ax2.set_title(f"MDD {mdd*100:.2f}%")
    ax2.grid(True)
    
    plt.tight_layout()
    png_path = OUT_DIR / "portfolio_3m.png"
    plt.savefig(png_path)
    
    send_telegram_report(summary, str(png_path))

if __name__ == "__main__":
    run()
