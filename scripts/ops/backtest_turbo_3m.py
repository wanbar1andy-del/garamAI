"""
Backtest Turbo 3M (Read-Only)
Running Quantum Hero Strategy (100% Compounding) on historical data (2025-10-01 ~ Now).
Non-intrusive: Writes only to logs/ops/backtest_3m_...
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

# Import existing engine
from scripts.quantum_hero_backtest import load_data, add_features, BacktestEngine, Q1Config, analyze_true_switches

# Setup Logging
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/ops/backtest_3m_{TIMESTAMP}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=[
    logging.FileHandler(OUT_DIR / "run.log", encoding='utf-8'),
    logging.StreamHandler()
])

def send_telegram_report(summary_text, image_path):
    token = os.environ.get("GARAM_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("GARAM_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        # Try secrets fallback logic similar to bot
        try:
            sec_path = PROJECT_ROOT / "config/telegram_secrets.json"
            if sec_path.exists():
                s = json.loads(sec_path.read_text(encoding='utf-8'))
                token = s.get("bot_token") or s.get("GARAM_TELEGRAM_BOT_TOKEN")
                chat_id = s.get("chat_id") or s.get("GARAM_TELEGRAM_CHAT_ID")
        except: pass
    
    if not token or not chat_id:
        logging.error("Telegram token not found. Skipping send.")
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

def run_backtest():
    logging.info("Starting Backtest (Turbo 3M)...")
    
    # Data Path
    data_path = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
    if not data_path.exists():
        logging.error(f"Data not found at {data_path}")
        return

    # Load Data
    df = load_data(str(data_path))
    df = add_features(df)
    
    # Config for Turbo (Quantum Hero default is 1-slot 100%)
    # Using 'SwitchHigh' logic (Most aggressive) or 'Hold' depending on Turbo definition.
    # User said "Turbo Rule (Full Compounding)". Usually assumes switching into winners.
    # I will use the "SwitchHigh" equivalent from quantum_hero_backtest main() which had Q0.95 dominance.
    # But for safety/stability validation, maybe Opt_G_SwitchHigh or even just Base.
    # Let's use Q1Config default "Base" but tuned for aggressiveness if needed.
    # Using specific 'SwitchHigh' params from q1 main:
    cfg = Q1Config(
        name="Turbo_3M_Compounding",
        start="2025-10-01",
        end=datetime.now().strftime("%Y-%m-%d"),
        execution_mode="CLOSE", # Close execution = Immediate action
        entry_quantile=0.70,
        switch_ratio=1.20,
        switch_abs_quantile=0.95, 
        min_hold_days=1, # Very aggressive
        fee_bps=2.0,
        slippage_bps=1.0,
        ban_on=False # Pure momentum
    )
    
    engine = BacktestEngine(df, cfg)
    eq_curve, trades = engine.run()
    
    # Analysis
    initial_capital = 100_000_000
    final_eq_norm = eq_curve[-1]['equity']
    final_capital = initial_capital * final_eq_norm
    total_ret = (final_eq_norm - 1.0)
    
    # MDD
    peak = -99999.0
    mdd = 0.0
    eq_vals = [x['equity'] for x in eq_curve]
    for v in eq_vals:
        if v > peak: peak = v
        dd = (v - peak) / peak
        if dd < mdd: mdd = dd
        
    # Stats
    n_trades = len(trades)
    win_trades = [t for t in trades if t['type'] == 'SELL' and engine.df[(engine.df['ticker']==t['ticker']) & (engine.df['date']==t['date'])].iloc[0]['close'] > t.get('entry_px', 0)] 
    # Logic for win rate needs pairing buys/sells.
    # Since quantum engine trades list doesn't explicitly link buy/sell in the list dict, 
    # we approximate via equity curve positive days or reconstruction.
    # Actually, simpler: just count days with positive return? No, trade-based.
    # Let's stick to Equity/MDD/CAGR.
    
    # Summary Report
    summary = f"""📊 **[가람] 터보룰 3개월 백테스트**
    
- 기간: 2025-10-01 ~ {cfg.end}
- 초기자본: 1억 원
- 최종자본: {final_capital:,.0f} 원
- 총수익률: {total_ret*100:+.2f}%
- MDD: {mdd*100:.2f}%
- 총 트레이드: {n_trades}회
- 전략: 100% 몰빵/복리 (Turbo)
- 수수료/슬리피지: 0.03% 반영
"""
    logging.info(summary)
    (OUT_DIR / "summary.txt").write_text(summary, encoding='utf-8')
    
    # Plotting
    dates = [x['date'] for x in eq_curve]
    nav = [x['equity'] * initial_capital for x in eq_curve]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
    
    # Equity
    ax1.plot(dates, nav, color='blue', label='Equity (KRW)')
    ax1.set_title(f"Turbo 3M Equity Curve (Final: {final_capital:,.0f} KRW)")
    ax1.grid(True)
    ax1.legend()
    # Format Y with commas
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # DD
    dd_curve = []
    r_peak = -1e9
    for v in nav:
        if v > r_peak: r_peak = v
        dd_curve.append((v - r_peak) / r_peak * 100)
        
    ax2.fill_between(dates, dd_curve, 0, color='red', alpha=0.3, label='Drawdown %')
    ax2.plot(dates, dd_curve, color='red', lw=1)
    ax2.set_title(f"Drawdown (MDD: {mdd*100:.2f}%)")
    ax2.grid(True)
    
    plt.tight_layout()
    png_path = OUT_DIR / "equity_3m.png"
    plt.savefig(png_path)
    logging.info(f"Saved plot to {png_path}")
    
    # Telegram
    send_telegram_report(summary, str(png_path))

if __name__ == "__main__":
    run_backtest()
