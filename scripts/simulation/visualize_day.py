import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def load_day_trades(path, label, color, target_date_str):
    if not path.exists():
        print(f"File not found: {path}")
        return None
    
    df = pd.read_csv(path)
    df['time'] = pd.to_datetime(df['time'])
    
    # Filter Date
    target_date = pd.Timestamp(target_date_str).date()
    df = df[df['time'].dt.date == target_date].copy()
    
    if df.empty:
        print(f"No trades for {label} on {target_date_str}")
        return None
    
    df = df.sort_values('time')
    
    # Reconstruct Intraday Equity Curve
    # Start at 0 PnL for the day
    
    curve = []
    # Add Start Point (09:00)
    start_time = pd.Timestamp(f"{target_date_str} 09:00:00")
    curve.append({"time": start_time, "cum_pnl": 0.0})
    
    current_pnl = 0.0
    
    # We want to see cumulative Net PnL for this day
    for _, row in df.iterrows():
        # Trade PnL is in 'net_pnl' column
        # Ideally, net_pnl is realized per trade.
        # But for 'Buy', net_pnl is usually -fee.
        # For 'Sell', net_pnl is (Price-Entry)*Qty - Fee.
        
        # Verify schema:
        # In v1.1 script:
        # BUY:  net_pnl = -cost_amt
        # SELL: net_pnl = gross_pnl - cost_amt
        
        # So summing net_pnl gives cumulative PnL.
        pnl = row['net_pnl']
        current_pnl += pnl
        curve.append({"time": row['time'], "cum_pnl": current_pnl})
        
    df_curve = pd.DataFrame(curve)
    
    # If last trade is before 15:30, extend line
    end_time = pd.Timestamp(f"{target_date_str} 15:30:00")
    if df_curve.iloc[-1]['time'] < end_time:
         df_curve = pd.concat([df_curve, pd.DataFrame([{"time": end_time, "cum_pnl": current_pnl}])], ignore_index=True)
         
    df_curve['label'] = label
    df_curve['color'] = color
    return df_curve

def run_viz(target_date="2025-12-15"):
    # Paths
    p_v0 = project_root / "results" / "audit" / "week1_v2" / "trades_week1_cost10.csv"
    p_v1 = project_root / "results" / "simulation" / "week1_v1" / "trades_week1_policy_v1.csv"
    p_v1_1 = project_root / "results" / "simulation" / "week1_v1_1" / "trades_week1_policy_v1_1.csv"
    
    curves = []
    
    c0 = load_day_trades(p_v0, "Policy v0 (Baseline)", "gray", target_date)
    if c0 is not None: curves.append(c0)
        
    c1 = load_day_trades(p_v1, "Policy v1 (Naive)", "blue", target_date)
    if c1 is not None: curves.append(c1)
        
    c1_1 = load_day_trades(p_v1_1, "Policy v1.1 (Optimized)", "red", target_date)
    if c1_1 is not None: curves.append(c1_1)
    
    # Plot
    plt.figure(figsize=(12, 6))
    
    for c in curves:
        # PnL to Return (on 10m capital)
        c['return'] = (c['cum_pnl'] / 10_000_000.0)
        
        plt.step(c['time'], c['return']*100, where='post', label=f"{c['label'].iloc[0]} ({c['return'].iloc[-1]*100:.2f}%)", 
                 color=c['color'].iloc[0], linewidth=2)
        
        # Add markers for trades
        plt.scatter(c['time'], c['return']*100, color=c['color'].iloc[0], s=20)
        
    plt.title(f"Intraday Comparison {target_date} (Policy v0 vs v1 vs v1.1)")
    plt.ylabel("Day Return (%)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.axhline(0, color='black', linewidth=1)
    
    out_path = project_root / "results" / "simulation" / f"day_{target_date.replace('-','')}_comparison.png"
    plt.savefig(out_path)
    print(f"Saved Chart: {out_path}")

if __name__ == "__main__":
    run_viz("2025-12-15")
