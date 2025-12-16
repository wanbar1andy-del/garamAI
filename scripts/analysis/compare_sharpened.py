import pandas as pd
from pathlib import Path
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS

def load_trades(strategy_name):
    path = PATHS.BASE_DIR / f"results/{strategy_name}/trades.csv"
    if not path.exists():
        print(f"Error: {path} not found")
        return None
    return pd.read_csv(path)

def calculate_metrics(df):
    if df is None or df.empty:
        return {}
        
    total_pnl = df['pnl'].sum()
    win_rate = (df['pnl'] > 0).mean()
    trade_count = len(df)
    avg_r = df['return_r'].mean()
    
    # Drawdown (Approximate from cumulative PnL)
    df = df.sort_values('exit_time')
    df['cum_pnl'] = df['pnl'].cumsum()
    df['peak'] = df['cum_pnl'].cummax()
    df['dd'] = df['cum_pnl'] - df['peak']
    max_dd = df['dd'].min()
    
    # Fast Cut Stats
    fast_cuts = df[df['exit_reason'] == 'FastCut']
    fast_cut_count = len(fast_cuts)
    fast_cut_pnl = fast_cuts['pnl'].sum()
    fast_cut_r_sum = fast_cuts['return_r'].sum()
    
    # Mode Stats (if available in exit_reason or separate log)
    # Currently exit_reason doesn't store Mode.
    # We can infer or just focus on Fast Cut for now.
    
    return {
        'Total PnL': total_pnl,
        'Win Rate': win_rate,
        'Trade Count': trade_count,
        'Avg R': avg_r,
        'Max DD (Trade)': max_dd,
        'Fast Cut Count': fast_cut_count,
        'Fast Cut PnL': fast_cut_pnl,
        'Fast Cut R Sum': fast_cut_r_sum
    }

def main():
    pure_v3 = load_trades("Pure_v3")
    sharpened_v3 = load_trades("Orb_V3")
    
    m_pure = calculate_metrics(pure_v3)
    m_sharp = calculate_metrics(sharpened_v3)
    
    print(f"{'Metric':<20} | {'Pure V3':<15} | {'Orb V3':<15} | {'Diff':<10}")
    print("-" * 70)
    
    metrics = ['Total PnL', 'Win Rate', 'Trade Count', 'Avg R', 'Max DD (Trade)']
    
    for m in metrics:
        v_pure = m_pure.get(m, 0)
        v_sharp = m_sharp.get(m, 0)
        
        if m == 'Total PnL' or m == 'Max DD (Trade)':
            diff = (v_sharp - v_pure) / abs(v_pure) * 100 if v_pure != 0 else 0
            print(f"{m:<20} | {v_pure:,.0f} KRW    | {v_sharp:,.0f} KRW    | {diff:+.1f}%")
        elif m == 'Win Rate':
            diff = (v_sharp - v_pure) * 100
            print(f"{m:<20} | {v_pure:.1%}        | {v_sharp:.1%}        | {diff:+.1f}pp")
        elif m == 'Avg R':
            diff = v_sharp - v_pure
            print(f"{m:<20} | {v_pure:.2f} R        | {v_sharp:.2f} R        | {diff:+.2f}R")
        else:
            diff = v_sharp - v_pure
            print(f"{m:<20} | {v_pure}          | {v_sharp}          | {diff:+}")
            
    print("-" * 70)
    print(f"Fast Cut Analysis (Sharpened V3):")
    print(f"Count: {m_sharp.get('Fast Cut Count', 0)}")
    print(f"PnL Sum: {m_sharp.get('Fast Cut PnL', 0):,.0f} KRW")
    print(f"R Sum: {m_sharp.get('Fast Cut R Sum', 0):.2f} R")
    
    # Acceptance Check
    pnl_ratio = m_sharp['Total PnL'] / m_pure['Total PnL'] if m_pure['Total PnL'] != 0 else 0
    print(f"\nAcceptance Check:")
    print(f"PnL Ratio: {pnl_ratio:.2f} (Target >= 0.8)")
    print(f"Max DD: {m_sharp['Max DD (Trade)']:,.0f} vs {m_pure['Max DD (Trade)']:,.0f} (Target <=)")
    print(f"Fast Cut R: {m_sharp.get('Fast Cut R Sum', 0):.2f} R (Target <= 0)")

if __name__ == "__main__":
    main()
