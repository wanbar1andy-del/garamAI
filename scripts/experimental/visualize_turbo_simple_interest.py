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

def run_simple_interest_simulation():
    print("=== Running Simple Interest (Non-Compounding) Turbo Visualization ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # Simulation Logic (Dynamic Turbo - Simple Interest)
    w1_base = 0.05
    w2_base = 0.95
    TURBO_MULT = 2.5
    ABS_MULT = 0.5
    
    initial_principal = 100_000_000.0
    accumulated_profit = 0.0
    
    dates = []
    equity_curve = [] # Principal + Profit
    
    crash_date = pd.Timestamp("2025-03-24")
    crash_val = 0
    
    # HMM
    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])

    for date, row in df.iterrows():
        recent_data = df_full_history.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent_data)
        
        r_e1 = row['ret_e1']
        r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
        
        # Exposure Logic (Fixed to Principal)
        curr_w1 = w1_base
        curr_w2 = w2_base
        
        if regime == 'BULL': curr_w2 *= TURBO_MULT
        elif regime == 'BEAR': curr_w1 *= ABS_MULT
        
        # Calculate PnL based on Principal ONLY
        # Exposure = Principal * Weights
        # We do NOT add accumulated_profit to exposure
        
        pnl_e1 = (initial_principal * curr_w1) * r_e1
        pnl_e2 = (initial_principal * curr_w2) * r_e2
        
        daily_pnl = pnl_e1 + pnl_e2
        accumulated_profit += daily_pnl
        
        current_total_equity = initial_principal + accumulated_profit
        
        dates.append(date)
        equity_curve.append(current_total_equity)
        
        if date.date() == crash_date.date():
            crash_val = current_total_equity

    # Stats
    final_equity = initial_principal + accumulated_profit
    total_ret_pct = (final_equity - initial_principal) / initial_principal * 100
    
    df_res = pd.DataFrame({'date': dates, 'equity': equity_curve})
    df_res.set_index('date', inplace=True)
    
    # MDD (on Total Equity)
    peak = df_res['equity'].cummax()
    dd = (df_res['equity'] - peak) / peak
    mdd_pct = dd.min() * 100
    
    print(f"Final Equity: {int(final_equity):,}")
    print(f"Return: {total_ret_pct:.2f}%")
    print(f"MDD: {mdd_pct:.2f}%")
    
    # Plotting
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df_res.index, df_res['equity'], color='#00aaff', linewidth=2, label='Turbo (Simple Interest)')
    
    # Annotate Crash
    if crash_val > 0:
        ax.scatter([crash_date], [crash_val], color='yellow', s=100, zorder=5)
        ax.annotate(f'Crash Defense', 
                    xy=(crash_date, crash_val), 
                    xytext=(crash_date, crash_val - 20_000_000),
                    arrowprops=dict(facecolor='white', shrink=0.05),
                    color='white', fontsize=10, ha='center')

    # Annotate Final
    ax.annotate(f'Final: {int(final_equity/10000):,}만원\n(+{total_ret_pct:.1f}%)', 
                xy=(df_res.index[-1], final_equity), 
                xytext=(df_res.index[-1], final_equity + 15_000_000),
                arrowprops=dict(facecolor='white', shrink=0.05),
                color='white', fontsize=11, fontweight='bold', ha='center')

    ax.set_title("1-Year Fixed Principal Simulation (No Profit Reinvestment)", fontsize=16, color='white', pad=20)
    ax.set_ylabel("Total Equity (KRW)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='upper left')
    
    # Format Y axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    # Save
    out_dir = Path(r"C:\Users\wanba\.gemini\antigravity\brain\9dc6d069-d531-4b67-8892-7dc3b3cdca78")
    out_path = out_dir / "final_turbo_simple_interest_graph.png"
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f"Graph Saved: {out_path}")

if __name__ == "__main__":
    run_simple_interest_simulation()
