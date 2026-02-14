"""
Operational Readiness Report Generator (Read-Only)
Purpose: Evaluate 'Operational Turbo' strategy suitability for live trading.
Criteria: GO/NO-GO based on MDD, Volatility, and Turnover.
Strategy: 5-Slot Portfolio (20% each) with Rebalancing.
"""
import os
import sys
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Import logic
from scripts.quantum_hero_backtest import load_data, add_features, compute_metrics

# Setup Logging
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/ops/ops_readiness_{TIMESTAMP}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=[
    logging.FileHandler(OUT_DIR / "run.log", encoding='utf-8'),
    logging.StreamHandler()
])

def send_telegram_report(summary_text, image_path):
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
    try:
        with open(image_path, 'rb') as f:
            data = {'chat_id': chat_id, 'caption': summary_text, 'parse_mode': 'Markdown'}
            files = {'photo': f}
            requests.post(url, data=data, files=files, timeout=30)
        logging.info("Telegram report sent.")
    except Exception as e:
        logging.error(f"Telegram fail: {e}")

class OpsReadinessEngine:
    def __init__(self, df, slots=5, initial_capital=100_000_000, entry_q=0.7):
        self.df = df
        self.slots = slots
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {} 
        self.equity_curve = []
        self.trades = []
        self.entry_threshold = 0.0
        
        # Calibration
        logging.info("Calibrating Threshold...")
        tmp = df.copy() 
        max_scores = []
        for date, g in tmp.groupby('date'):
            scores = []
            for _, r in g.iterrows():
                _, _, s = compute_metrics(r)
                scores.append(s)
            if scores: max_scores.append(max(scores))
        
        if max_scores:
            self.entry_threshold = pd.Series(max_scores).quantile(entry_q)
        else:
            self.entry_threshold = 0.5
            
        logging.info(f"Entry Threshold (Q{entry_q}): {self.entry_threshold:.4f}")

    def run(self):
        dates = sorted(self.df["date"].unique())
        dates = [d for d in dates if d >= pd.Timestamp("2025-10-01")]
        
        logging.info(f"Running Simulation ({len(dates)} days)...")
        fee = 0.002
        
        for d in dates:
            day_data = self.df[self.df["date"] == d].copy()
            
            # MTM
            holdings_val = 0.0
            for tkr in list(self.positions.keys()):
                row = day_data[day_data['ticker'] == tkr]
                if not row.empty:
                    self.positions[tkr]['mark_px'] = float(row.iloc[0]['close'])
                holdings_val += self.positions[tkr]['shares'] * self.positions[tkr]['mark_px']
            
            curr_equity = self.cash + holdings_val
            self.equity_curve.append({'date': d, 'equity': curr_equity})
            
            # Rank
            candidates = []
            for _, r in day_data.iterrows():
                _, _, score = compute_metrics(r)
                if score > 0:
                    candidates.append({'ticker': r['ticker'], 'close': r['close'], 'score': score})
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            valid = [c for c in candidates if c['score'] >= self.entry_threshold]
            targets = valid[:self.slots]
            target_tkrs = set(t['ticker'] for t in targets)
            
            # Sell
            for tkr in list(self.positions.keys()):
                if tkr not in target_tkrs:
                    px = self.positions[tkr]['mark_px']
                    amt = self.positions[tkr]['shares'] * px
                    self.cash += amt * (1 - fee)
                    del self.positions[tkr]
                    self.trades.append({'date': d, 'type': 'SELL'})
            
            # Buy
            active_slots = len(self.positions)
            free = self.slots - active_slots
            if free > 0:
                per_slot = curr_equity / self.slots
                for t in targets:
                    if t['ticker'] not in self.positions:
                        if self.cash < per_slot * 0.5: break
                        use_cash = min(self.cash, per_slot)
                        shares = int(use_cash / t['close'])
                        if shares > 0:
                            cost = shares * t['close']
                            self.cash -= cost * (1 + fee)
                            self.positions[t['ticker']] = {'shares': shares, 'mark_px': t['close']}
                            self.trades.append({'date': d, 'type': 'BUY'})
                            
        return self.equity_curve, self.trades

def calculate_kpis(eq, trades, initial_cap):
    df = pd.DataFrame(eq)
    df['date'] = pd.to_datetime(df['date'])
    df['ret'] = df['equity'].pct_change().fillna(0)
    
    # 1. Return
    final_eq = df.iloc[-1]['equity']
    total_ret = (final_eq / initial_cap) - 1.0
    
    # 2. MDD
    roll_max = df['equity'].cummax()
    dd = (df['equity'] - roll_max) / roll_max
    mdd = dd.min()
    
    # 3. Max Underwater (Days)
    is_underwater = dd < 0
    uw_groups = (is_underwater != is_underwater.shift()).cumsum()
    uw_days = df[is_underwater].groupby(uw_groups)['date'].agg(lambda x: (x.max() - x.min()).days)
    max_uw_days = uw_days.max() if not uw_days.empty else 0
    
    # 4. Volatility (Daily Std)
    vol_daily = df['ret'].std()
    vol_annual = vol_daily * np.sqrt(252)
    
    # 5. Turnover
    # Simple proxy: Total Trades / (Days * Slots) or just raw count
    # User asked for "Turnover/Switch Count"
    switch_count = len(trades)
    
    return {
        "final_cap": final_eq,
        "total_ret": total_ret,
        "mdd": mdd,
        "max_uw_days": max_uw_days,
        "vol_annual": vol_annual,
        "switch_count": switch_count,
        "df": df,
        "dd_series": dd
    }

def run():
    # Parse Args
    lookback_days = 90
    if len(sys.argv) > 1:
        try:
            lookback_days = int(sys.argv[1])
        except: pass
    
    # Calculate Start Date
    start_dt = datetime.now() - timedelta(days=lookback_days)
    start_date_str = start_dt.strftime("%Y-%m-%d")
    
    # Data
    data_path = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
    if not data_path.exists(): return
    
    df = load_data(str(data_path))
    df = add_features(df)
    
    # Filter Date
    # Note: df['date'] is datetime64
    df = df[df['date'] >= pd.Timestamp(start_date_str)]
    
    if df.empty:
        logging.error("No data for period.")
        return

    # Run
    sim = OpsReadinessEngine(df, slots=5, initial_capital=100_000_000)
    eq, trades = sim.run()
    
    if not eq:
        logging.error("No trades/equity generated.")
        return

    # KPIs
    kpi = calculate_kpis(eq, trades, 100_000_000)
    
    # GO/NO-GO Logic
    verdict = "GO"
    risk_factors = []
    
    if kpi['mdd'] < -0.12: # MDD > 12% -> NO-GO
        verdict = "NO-GO"
        risk_factors.append(f"MDD 초과 ({kpi['mdd']*100:.1f}% > -12%)")
        
    if kpi['max_uw_days'] > 30: # 30 days underwater warning
        risk_factors.append(f"회복기간 장기화 ({kpi['max_uw_days']}일)")
        
    if kpi['vol_annual'] > 0.4: # Annual Vol > 40% warning
        risk_factors.append(f"변동성 과다 ({kpi['vol_annual']*100:.1f}%)")

    if not risk_factors and verdict == "GO":
        reason = "모든 운영 기준 충족 (안전)"
    else:
        reason = ", ".join(risk_factors)
        if verdict == "GO": verdict = "CONDITIONAL GO" # Warnings present
        
    # Telegram Message
    summary = f"""📋 **[가람] 운영 적합성 리포트 (최근 {lookback_days}일)**
    
⚖️ **판정: {verdict}**
❓ **사유**: {reason}

📊 **주요 지표 ({start_date_str} ~ Now)**
1. **수익률**: {kpi['total_ret']*100:+.2f}% (1억 -> {kpi['final_cap']/100000000:.2f}억)
2. **MDD**: {kpi['mdd']*100:.2f}% (기준 -12% 이하)
3. **최대 낙폭기간**: {kpi['max_uw_days']}일
4. **연변동성**: {kpi['vol_annual']*100:.1f}%
5. **스위칭**: {kpi['switch_count']}회

💡 **전보**: {lookback_days}일간의 5분할 포트폴리오(Operating Turbo) 시뮬레이션 결과입니다.
"""
    logging.info(summary)
    (OUT_DIR / "summary.txt").write_text(summary, encoding='utf-8')

    # Plotting (2 Charts)
    df = kpi['df']
    dd = kpi['dd_series']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={'height_ratios': [1, 1]})
    
    # Chart 1: Equity
    ax1.plot(df['date'], df['equity'], color='blue', label='Equity (KRW)')
    ax1.set_title(f"Curve: 100M -> {kpi['final_cap']/1_000_000:.1f}M (+{kpi['total_ret']*100:.1f}%)")
    ax1.grid(True)
    ax1.legend()
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # Chart 2: Drawdown
    ax2.fill_between(df['date'], dd * 100, 0, color='red', alpha=0.3)
    ax2.plot(df['date'], dd * 100, color='red', lw=1)
    ax2.axhline(-12, color='black', linestyle='--', label='NO-GO Limit (-12%)')
    ax2.set_title(f"Drawdown Risk (Max: {kpi['mdd']*100:.2f}%)")
    ax2.set_ylabel("Drawdown %")
    ax2.grid(True)
    ax2.legend()
    
    plt.tight_layout()
    png_path = OUT_DIR / "ops_readiness.png"
    plt.savefig(png_path)
    
    send_telegram_report(summary, str(png_path))

if __name__ == "__main__":
    run()
