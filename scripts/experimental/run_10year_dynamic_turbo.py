import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Setup Path
sys.path.append(os.path.abspath("C:/garam/garam"))

try:
    from config import PATHS
except ImportError:
    from garam.config import PATHS

from garam.engine.components.hmm_detector import HMMRegimeDetector

def load_data():
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    if not kospi_path.exists():
        raise FileNotFoundError(f"KOSPI data not found at {kospi_path}")
        
    df_mkt = pd.read_csv(kospi_path)
    col_map = {c: c.lower() for c in df_mkt.columns}
    df_mkt.rename(columns=col_map, inplace=True)
    date_col = 'timestamp' if 'timestamp' in df_mkt.columns else 'date'
    df_mkt[date_col] = pd.to_datetime(df_mkt[date_col])
    df_mkt.set_index(date_col, inplace=True)
    df_mkt.sort_index(inplace=True)
    
    # Calculate Market Return
    df_mkt['ret_mkt'] = df_mkt['close'].pct_change().fillna(0.0)
    
    # Filter for last 10 years (approx 2015~2025)
    start_date = pd.Timestamp("2015-01-01")
    df_10y = df_mkt[df_mkt.index >= start_date].copy()
    
    return df_10y, df_mkt

def run_10year_simulation():
    print("=== Running 10-Year Dynamic Turbo Backtest (2015-2025) ===")
    try:
        df, df_full = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # Configuration (Dynamic Turbo Final)
    W1_BASE = 0.05
    W2_BASE = 0.95
    TURBO = 2.5
    
    # HMM Init (Train on pre-2015 data)
    print("Training HMM on data before 2015...")
    train_data = df_full[df_full.index < df.index[0]]['close']
    hmm = HMMRegimeDetector()
    hmm.train(train_data)
    
    equity = 100_000_000.0
    initial_equity = equity
    
    dates = []
    equity_curve = []
    regimes = []
    
    peak = equity
    mdd = 0.0
    
    print(f"Simulation Start: {df.index[0].date()} - End: {df.index[-1].date()}")
    
    for date, row in df.iterrows():
        # Predict Regime
        # Use expanding window or rolling? HMM usually needs only recent window for prediction if internal state is stateless,
        # but GaussianHMM in implementation likely predicts based on sequence passed.
        # Passing last 50 days is standard in our system.
        recent_data = df_full.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        regimes.append(regime)
        
        # Returns
        r_mkt = row['ret_mkt']
        r_e2 = 0.0 if regime == 'BEAR' else r_mkt # Engine 2 safety
        
        # Engine 1 Proxy: Assume E1 tracks Market (Beta=1) for this 10y test
        # Since we don't have 10y E1 active data.
        r_e1 = r_mkt 
        
        # Dynamic Turbo Logic
        w1 = W1_BASE
        w2 = W2_BASE
        
        if regime == 'BULL':
            w2 *= TURBO # Boost Market Exposure
        elif regime == 'BEAR':
            w1 *= 0.5 # Hedge Active
            
        blended_ret = w1 * r_e1 + w2 * r_e2
        equity *= (1.0 + blended_ret)
        
        dates.append(date)
        equity_curve.append(equity)
        
        if equity > peak: peak = equity
        dd = (equity - peak) / peak
        if dd < mdd: mdd = dd

    # Stats
    total_ret = (equity - initial_equity) / initial_equity
    cagr = (equity / initial_equity) ** (1/10) - 1.0 # Approx 10 years
    
    print(f"Final Equity: {int(equity):,}")
    print(f"Total Return: {total_ret*100:.2f}%")
    print(f"CAGR: {cagr*100:.2f}%")
    print(f"MDD: {mdd*100:.2f}%")
    
    # Plot
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Equity Curve
    ax1.plot(dates, equity_curve, color='#00ff9d', linewidth=1.5, label='Dynamic Turbo Portfolio')
    ax1.set_title("10-Year Backtest: Dynamic Turbo (2015-2025)", fontsize=16, color='white')
    ax1.set_ylabel("Equity (KRW)", fontsize=12)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.legend()
    
    # Annotate significant points
    # Max Equity
    max_idx = np.argmax(equity_curve)
    ax1.annotate(f'Peak: {int(equity_curve[max_idx]/10000):,}만원', 
                 xy=(dates[max_idx], equity_curve[max_idx]),
                 xytext=(dates[max_idx], equity_curve[max_idx] * 1.2),
                 arrowprops=dict(facecolor='white', shrink=0.05), color='white', ha='center')

    # Regime Strip
    # Map regimes to colors: BULL=Green, SIDEWAYS=Gray, BEAR=Red
    regime_colors = {'BULL': 'green', 'SIDEWAYS': 'gray', 'BEAR': 'red'}
    colors = [regime_colors[r] for r in regimes]
    
    # We can't easily plot a colored strip with simple plot, use bar or fill_between?
    # Approximating with a scatter or just simple step plot implies numeric mapping
    # Let's simple check counts
    bull_count = regimes.count('BULL')
    bear_count = regimes.count('BEAR')
    print(f"Regime Dist: Bull={bull_count}, Bear={bear_count}, Side={len(regimes)-bull_count-bear_count}")
    
    # Save
    out_dir = Path(r"C:\Users\wanba\.gemini\antigravity\brain\9dc6d069-d531-4b67-8892-7dc3b3cdca78")
    out_path = out_dir / "10year_dynamic_turbo_simulation.png"
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f"Graph Saved: {out_path}")

if __name__ == "__main__":
    run_10year_simulation()
