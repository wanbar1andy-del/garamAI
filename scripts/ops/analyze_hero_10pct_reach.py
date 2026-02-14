"""
Hero 10% Reach Analyzer (Operational Edge Verification)
Purpose: Measure if "Hero" stocks (Top 1 by Score) actually hit +10% within N days.
Logic:
    - Identify Daily Hero (EOD Scanning).
    - Enter at Day Close.
    - Check forward N days for +10% High or Close.
    - Metrics: Hit Rate, Time-to-Hit, MAE.
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path

# Setup Project Path
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Reuse Logic (Scoring)
try:
    from scripts.quantum_hero_backtest import load_data, add_features, compute_metrics
except ImportError:
    # Fallback or error if not found (should exist per check)
    logging.error("Could not import scripts.quantum_hero_backtest")
    sys.exit(1)

# Setup Logging
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/ops/hero_10pct_reach_{TIMESTAMP}"
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

def run_analysis():
    # 1. Config
    horizons = [5, 10, 15, 20] # Days to look forward
    target_return = 0.10 # 10%
    data_path = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
    
    # 2. Load Data
    logging.info("Loading 60-day data...")
    if not data_path.exists():
        logging.error(f"Data path not found: {data_path}")
        return

    df = load_data(str(data_path))
    df = add_features(df)
    
    # Ensure Date type
    df['date'] = pd.to_datetime(df['date'])
    dates = sorted(df['date'].unique())
    
    logging.info(f"Loaded {len(df)} rows, {len(dates)} trading days.")

    # 3. Identify Heroes & Check Outcomes
    results = [] # {date, hero, entry_px, max_h_5, max_c_5, hit_5, ...}
    
    # We need to iterate until (Last Day - Max Horizon) to have full ground truth
    # But for "Recent" analysis, we accept censored data (not yet hit) as False or Pending.
    # Let's run for all dates where we can pick a hero.
    
    # Pre-calculate scores per day? optimized loop
    # Group by Date
    daily_groups = df.groupby('date')
    
    for d_idx, d in enumerate(dates):
        # Skip if not enough future data for smallest horizon? 
        # We'll just check what's available.
        
        # 3.1 Ranking
        day_df = daily_groups.get_group(d)
        candidates = []
        for _, r in day_df.iterrows():
            # Use safe compute
            try:
                _, _, score = compute_metrics(r)
                if np.isnan(score): score = -999
                candidates.append({'ticker': r['ticker'], 'score': score, 'close': r['close']})
            except: pass
            
        if not candidates: continue
        
        # Sort desc
        candidates.sort(key=lambda x: x['score'], reverse=True)
        hero = candidates[0]
        
        if hero['score'] <= 0: continue # No valid hero
        
        # 3.2 Entry
        entry_px = hero['close']
        ticker = hero['ticker']
        
        # 3.3 Forward Check
        # Get future prices for this ticker
        # Efficiency: slicing huge DF is slow. 
        # Better: Filter DF by ticker first? No, we scan day by day.
        # Querying future days:
        future_dates = dates[d_idx+1 : d_idx+1+max(horizons)]
        
        # Only fetch future data for this ticker (Optimization: Do this efficiently)
        # Using boolean mask on full DF is slow inside loop.
        # But 60 days * 400 symbols is small-ish (24k rows). It's fine.
        
        # Let's filter by ticker first, then slice by date index.
        # Wait, grouping by ticker first globally is faster.
        # BUT finding hero is day-by-day.
        # HYBRID: Identify Heroes first (all days), then process outcomes by ticker.
        
        results.append({
            'date': d,
            'ticker': ticker,
            'entry_px': entry_px,
            'd_idx': d_idx
        })

    # Transform to DF for outcome processing
    res_df = pd.DataFrame(results)
    if res_df.empty:
        logging.error("No heroes found.")
        return

    logging.info(f" Identified {len(res_df)} daily heroes. Checking outcomes...")
    
    # Process Outcomes grouped by Ticker to avoid repeated scans
    # Need global ticker data map
    df_by_ticker = {t: g.sort_values('date').set_index('date') for t, g in df.groupby('ticker')}
    
    final_rows = []
    
    for _, row in res_df.iterrows():
        tkr = row['ticker']
        entry_date = row['date']
        entry_px = row['entry_px']
        
        if tkr not in df_by_ticker:
            continue
            
        tdf = df_by_ticker[tkr]
        # Get future rows
        future_tdf = tdf[tdf.index > entry_date]
        if future_tdf.empty:
            continue
            
        # Analyze Horizons
        record = row.to_dict()
        
        # Find first index where Hit occurs
        # Intraday Hit
        # Vectorized check
        highs = future_tdf['high'].values
        closes = future_tdf['close'].values
        lows = future_tdf['low'].values
        # timestamps = future_tdf.index
        
        # We need "Trading Days passed"
        # Since tdf is indexed by date (daily), row 0 is T+1.
        
        # Calculate Hits per Horizon
        intraday_hit_idx = np.where(highs >= entry_px * (1 + target_return))[0]
        close_hit_idx = np.where(closes >= entry_px * (1 + target_return))[0]
        
        tth_intraday = intraday_hit_idx[0] + 1 if len(intraday_hit_idx) > 0 else 999
        tth_close = close_hit_idx[0] + 1 if len(close_hit_idx) > 0 else 999
        
        record['tth_intraday'] = tth_intraday
        record['tth_close'] = tth_close
        
        # MAE (Max Adverse Excursion) in N=20 (or max available)
        # Min(Low) / Entry - 1
        n_mae_limit = 20
        mae_window_lows = lows[:min(len(lows), n_mae_limit)]
        if len(mae_window_lows) > 0:
            min_l = np.min(mae_window_lows)
            record['MAE_20'] = (min_l / entry_px) - 1.0
        else:
            record['MAE_20'] = 0.0

        for h in horizons:
            # Check availability
            # T+1 is index 0. T+H is index H-1.
            # So looking at slice [:h]
            
            # Hit Flags
            record[f'hit_intra_{h}'] = (tth_intraday <= h)
            record[f'hit_close_{h}'] = (tth_close <= h)
            
        final_rows.append(record)

    analysis_df = pd.DataFrame(final_rows)
    analysis_df.to_csv(OUT_DIR / "detail.csv", index=False)
    
    # 4. Aggregate & Visualize
    
    # 4.1 Hit Rates
    stats = []
    for h in horizons:
        # Filter: Exclude days where we don't have enough data?
        # User said "Result of verification".
        # If we are at the end of dataset, we technically don't know yet.
        # But user wants "Reachability". Including censored data lowers rate unfairly.
        # But excluding them reduces recency.
        # Standard: Include all, but note that recent days naturally fail.
        # CORRECT: Filter dataset. Only count entries where (Today - EntryDate) >= H or Hit happened.
        # Simplification: Use full dataset but be aware of edge drop-off.
        # However, for a 60-day dataset, T+20 cuts off 1/3 data.
        # Let's just report Raw Rate on valid samples if possible, or All.
        # Let's stick to "All valid samples for that horizon" (i.e. exclude last H days).
        
        # Create mask for valid horizon
        # For a specific row, valid if (Last_Date_In_DB - Entry_Date).days >= H? No, trading days.
        # We can approximate: if (total_dates - d_idx) > h.
        
        total_days_count = len(dates)
        valid_mask = (total_days_count - 1 - analysis_df['d_idx']) >= h
        subset = analysis_df[valid_mask]
        
        if subset.empty:
            intra_rate = 0.0
            close_rate = 0.0
        else:
            intra_rate = subset[f'hit_intra_{h}'].mean() * 100
            close_rate = subset[f'hit_close_{h}'].mean() * 100
            
        stats.append({
            'Horizon': h, 
            'Intraday %': intra_rate, 
            'Close %': close_rate,
            'Samples': len(subset)
        })
        
    stats_df = pd.DataFrame(stats)
    
    # 4.2 Time to Hit Stats (Only Hits)
    hits_intra = analysis_df[analysis_df['tth_intraday'] <= 20]
    hits_close = analysis_df[analysis_df['tth_close'] <= 20]
    
    median_tth = hits_intra['tth_intraday'].median() if not hits_intra.empty else 0
    median_mae = analysis_df['MAE_20'].median() * 100
    
    # Generate Plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Hit Rate Bar Chart
    x = np.arange(len(horizons))
    width = 0.35
    ax1.bar(x - width/2, stats_df['Intraday %'], width, label='Intraday High > 10%')
    ax1.bar(x + width/2, stats_df['Close %'], width, label='Close > 10%')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"T+{h}" for h in horizons])
    ax1.set_ylabel('Hit Rate (%)')
    ax1.set_title('Hero 10% Hit Probability by Horizon')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    for i, v in enumerate(stats_df['Intraday %']):
        ax1.text(i - width/2, v + 1, f"{v:.1f}%", ha='center')
    for i, v in enumerate(stats_df['Close %']):
        ax1.text(i + width/2, v + 1, f"{v:.1f}%", ha='center')

    # Plot 2: Time-to-Hit Histogram (Intraday)
    if not hits_intra.empty:
        sns.histplot(hits_intra['tth_intraday'], bins=np.arange(1, 22)-0.5, ax=ax2, kde=True, color='purple')
        ax2.set_xlabel('Trading Days to Hit +10%')
        ax2.set_title(f'Time-to-Hit Distribution (Median: {median_tth:.1f} days)')
        ax2.set_xticks(horizons)
    else:
        ax2.text(0.5, 0.5, "No Hits Found", ha='center')
        
    plt.tight_layout()
    png_path = OUT_DIR / "hero_10pct_reach.png"
    plt.savefig(png_path)
    
    # 5. Report
    summary = f"""🚀 **[가람] Hero 10% 도달 확률 분석 (최근 60일)**

🎯 **목표**: 일별 Hero(Score 1위) 선정 후, **진입가(종가) 대비 +10% 도달 여부** 검증.

📊 **분석 요약 (Median)**
*   **Intraday Hit (T+10)**: {stats_df.loc[stats_df['Horizon']==10, 'Intraday %'].values[0]:.1f}%
*   **Close Hit (T+10)**: {stats_df.loc[stats_df['Horizon']==10, 'Close %'].values[0]:.1f}%
*   **Time-to-Hit**: {median_tth:.1f} 거래일
*   **MAE (최대손실폭)**: {median_mae:.2f}% (중위값)

📈 **Horizon별 확률 (Intraday / Close)**
*   **T+5**: {stats_df.loc[0,'Intraday %']:.1f}% / {stats_df.loc[0,'Close %']:.1f}%
*   **T+10**: {stats_df.loc[1,'Intraday %']:.1f}% / {stats_df.loc[1,'Close %']:.1f}%
*   **T+20**: {stats_df.loc[3,'Intraday %']:.1f}% / {stats_df.loc[3,'Close %']:.1f}%

📝 **결론**: Hero 선정 후 10% 수익을 위해선 평균 **{median_tth:.0f}일** 보유가 필요하며, 이 기간 동안 **{median_mae:.1f}%** 수준의 평가손실을 견뎌야 합니다.
"""
    logging.info(summary)
    (OUT_DIR / "summary.txt").write_text(summary, encoding='utf-8')
    
    send_telegram_report(summary, str(png_path))

if __name__ == "__main__":
    run_analysis()
