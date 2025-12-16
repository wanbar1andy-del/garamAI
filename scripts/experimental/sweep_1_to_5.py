import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

def run_sweep_1_to_5():
    print("=== Micro-Allocation Sweep (1% ~ 5%) ===")
    try:
        df, df_full_history = load_data()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    ratios = [0.01, 0.02, 0.03, 0.04, 0.05]
    
    hmm = HMMRegimeDetector()
    hmm.train(df_full_history[df_full_history.index < df.index[0]]['close'])
    
    results = []
    
    best_ret = -999
    best_equity_curve = None
    best_ratio = 0
    
    for r1 in ratios:
        w1_fixed = r1
        w2_fixed = 1.0 - w1_fixed
        
        equity = 100_000_000.0
        peak = equity
        mdd = 0.0
        
        eq_curve = []
        
        for date, row in df.iterrows():
            recent_data = df_full_history.loc[:date]['close'].tail(50)
            regime = hmm.predict_regime(recent_data)
            
            r_e1 = row['ret_e1']
            r_e2 = 0.0 if regime == 'BEAR' else row['ret_mkt']
            
            blended_ret = w1_fixed * r_e1 + w2_fixed * r_e2
            equity *= (1.0 + blended_ret)
            eq_curve.append(equity)
            
            if equity > peak: peak = equity
            dd = (equity - peak) / peak
            if dd < mdd: mdd = dd
            
        final_ret = (equity - 100_000_000) / 100_000_000
        
        results.append({
            "Engine1_Ratio": f"{int(r1*100)}%",
            "Total_Return": f"{final_ret*100:.2f}%",
            "MDD": f"{mdd*100:.2f}%",
            "Final_Equity": int(equity)
        })
        
        if final_ret > best_ret:
            best_ret = final_ret
            best_equity_curve = pd.DataFrame({'date': df.index, 'equity': eq_curve}).set_index('date')
            best_ratio = int(r1*100)

    # Print Text Report
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    
    # Plot Best
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(best_equity_curve.index, best_equity_curve['equity'], color='#00ff9d', linewidth=2, label=f'Best Portfolio (E1={best_ratio}%)')
    
    # Annotate Crash
    CRASH_DATE = pd.Timestamp("2025-03-24")
    if CRASH_DATE in best_equity_curve.index:
        c_val = best_equity_curve.loc[CRASH_DATE]['equity']
        ax.scatter([CRASH_DATE], [c_val], color='red', s=100, zorder=5)
        ax.annotate(f'Crash Defense', xy=(CRASH_DATE, c_val), xytext=(CRASH_DATE, c_val - 20_000_000),
                    arrowprops=dict(facecolor='white', shrink=0.05), color='white', ha='center')

    final_eq = best_equity_curve['equity'].iloc[-1]
    ax.annotate(f'Final: {int(final_eq/10000):,}만원\n(+{best_ret*100:.1f}%)', 
                xy=(best_equity_curve.index[-1], final_eq), 
                xytext=(best_equity_curve.index[-1], final_eq + 10_000_000),
                arrowprops=dict(facecolor='white', shrink=0.05), color='white', fontweight='bold', ha='center')

    ax.set_title(f"Best Micro-Allocation Optimization (E1={best_ratio}%)", fontsize=16, pad=20)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend()
    
    out_dir = Path(r"C:\Users\wanba\.gemini\antigravity\brain\9dc6d069-d531-4b67-8892-7dc3b3cdca78")
    out_path = out_dir / "micro_allocation_1to5_graph.png"
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    print(f"Graph Saved: {out_path}")

if __name__ == "__main__":
    run_sweep_1_to_5()
