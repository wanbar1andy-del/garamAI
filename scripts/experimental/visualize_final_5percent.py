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
    e1_path = "C:/garam/garam/simulation_1year_comparison.csv"
    if not os.path.exists(e1_path):
        raise FileNotFoundError(f"Engine 1 data not found at {e1_path}")
    
    df_e1 = pd.read_csv(e1_path)
    df_e1['date'] = pd.to_datetime(df_e1['date'])
    df_e1.set_index('date', inplace=True)
    df_e1['ret_e1'] = df_e1['Original'].pct_change().fillna(0.0)
    
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    df_mkt = pd.read_csv(kospi_path)
    col_map = {c: c.lower() for c in df_mkt.columns}
    df_mkt.rename(columns=col_map, inplace=True)
    date_col = 'timestamp' if 'timestamp' in df_mkt.columns else 'date'
    df_mkt[date_col] = pd.to_datetime(df_mkt[date_col])
    df_mkt.set_index(date_col, inplace=True)
    df_mkt.sort_index(inplace=True)
    df_mkt['ret_mkt'] = df_mkt['close'].pct_change().fillna(0.0)
    
    df = df_e1[['ret_e1']].join(df_mkt[['close', 'ret_mkt']], how='inner')
    return df, df_mkt

def run_visualization():
    print("=== Running Final 5% Visualization ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # Simulation Logic (Fixed 5%)
    w1_fixed = 0.05
    w2_fixed = 0.95
    
    equity = 100_000_000.0
    equity_curve = []
    dates = []
    
    crash_date = pd.Timestamp("2025-03-24")
    crash_val = 0
    
    # HMM (Needed for E2 logic: Bear -> Cash)
    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])

    for date, row in df.iterrows():
        recent_data = df_full_history.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        
        r_e1 = row['ret_e1']
        r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
        
        blended_ret = w1_fixed * r_e1 + w2_fixed * r_e2
        equity *= (1.0 + blended_ret)
        
        dates.append(date)
        equity_curve.append(equity)
        
        if date.date() == crash_date.date():
            crash_val = equity

    # Stats
    final_equity = equity
    total_ret_pct = (final_equity - 100_000_000) / 100_000_000 * 100
    profit = final_equity - 100_000_000
    
    df_res = pd.DataFrame({'date': dates, 'equity': equity_curve})
    df_res.set_index('date', inplace=True)
    
    # MDD
    peak = df_res['equity'].cummax()
    dd = (df_res['equity'] - peak) / peak
    mdd_pct = dd.min() * 100
    
    print(f"Final Equity: {int(final_equity):,}")
    print(f"Return: {total_ret_pct:.2f}%")
    print(f"MDD: {mdd_pct:.2f}%")
    
    # Plotting
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df_res.index, df_res['equity'], color='#00ff9d', linewidth=2, label='Portfolio (Fixed 5%)')
    
    # Annotate Crash
    if crash_val > 0:
        ax.scatter([crash_date], [crash_val], color='red', s=100, zorder=5)
        ax.annotate(f'Crash Defense\n(-0.96%)', 
                    xy=(crash_date, crash_val), 
                    xytext=(crash_date, crash_val - 20_000_000),
                    arrowprops=dict(facecolor='white', shrink=0.05),
                    color='white', fontsize=10, ha='center')

    # Annotate Final
    ax.annotate(f'Final: {int(final_equity/10000):,}만원\n(+{total_ret_pct:.1f}%)', 
                xy=(df_res.index[-1], final_equity), 
                xytext=(df_res.index[-1], final_equity + 10_000_000),
                arrowprops=dict(facecolor='white', shrink=0.05),
                color='white', fontsize=11, fontweight='bold', ha='center')

    ax.set_title("1-Year Simulation: Fixed 5% Active Allocation", fontsize=16, color='white', pad=20)
    ax.set_ylabel("Total Equity (KRW)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='upper left')
    
    # Format Y axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    # Save
    out_dir = Path(r"C:\Users\wanba\.gemini\antigravity\brain\9dc6d069-d531-4b67-8892-7dc3b3cdca78")
    out_path = out_dir / "final_5percent_simulation.png"
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f"Graph Saved: {out_path}")

if __name__ == "__main__":
    run_visualization()
