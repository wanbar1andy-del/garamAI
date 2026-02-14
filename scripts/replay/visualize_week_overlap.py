import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def simulate_day_pnl(target_date_str):
    target_date = pd.to_datetime(target_date_str)
    day_dir = project_root / "results" / "labels" / f"day={target_date_str}"
    seg_path = day_dir / "hero_segments.csv"
    
    if not seg_path.exists():
        return None

    # Load Segments
    df_seg = pd.read_csv(seg_path)
    df_seg['start_time'] = pd.to_datetime(df_seg['start_time'])
    df_seg['end_time'] = pd.to_datetime(df_seg['end_time'])
    df_seg.sort_values('start_time', inplace=True)
    
    # Simulation Settings
    initial_capital = 10_000_000.0
    capital = initial_capital
    cost_rate = 0.0010 # 10bps
    
    # Session Index
    session_idx = pd.date_range(f"{target_date_str} 09:00", f"{target_date_str} 15:30", freq="1T")
    
    # Pre-load prices
    active_symbols = df_seg['symbol'].unique()
    price_cache = {}
    for sym in active_symbols:
        p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
        if p.exists():
            # Minimal load
            try:
                # Assuming simplified load to avoid huge overhead
                d = pd.read_csv(p, usecols=['date', 'close'])
                # Quick parse logic
                d['date_str'] = d['date'].astype(str)
                d = d[d['date_str'].str.startswith(target_date.strftime('%Y%m%d'))].copy()
                d['date'] = pd.to_datetime(d['date_str'], format='%Y%m%d%H%M%S')
                d = d.set_index('date')['close']
                price_cache[sym] = d
            except:
                pass

    # Timeline Construction
    target_timeline = pd.Series(index=session_idx, dtype=object)
    for _, seg in df_seg.iterrows():
        rng = pd.date_range(seg['start_time'], seg['end_time'], freq="1T")
        # Greedy overwrite
        target_timeline.loc[rng] = seg['symbol']
    
    # Simulation Loop
    current_holding = None
    shares = 0
    entry_price = 0.0
    
    equity_curve = []
    
    for t in session_idx:
        # Exit?
        if current_holding:
            target = target_timeline.get(t)
            if target != current_holding:
                price_series = price_cache.get(current_holding)
                exit_price = entry_price
                if price_series is not None:
                    exit_price = price_series.asof(t) if pd.notna(price_series.asof(t)) else entry_price
                
                gross = shares * exit_price
                capital = gross * (1 - cost_rate/2)
                current_holding = None
                shares = 0
        
        # Entry?
        if not current_holding:
            target = target_timeline.get(t)
            if isinstance(target, str) or isinstance(target, int):
                target = str(target).zfill(6)
                price_series = price_cache.get(target)
                if price_series is not None:
                    curr_p = price_series.asof(t)
                    if pd.notna(curr_p) and curr_p > 0:
                        cost_amt = capital * (cost_rate/2)
                        shares = (capital - cost_amt) / curr_p
                        entry_price = curr_p
                        current_holding = target
        
        # MTM
        val = capital
        if current_holding:
             price_series = price_cache.get(current_holding)
             curr_p = price_series.asof(t) if price_series is not None else entry_price
             if pd.isna(curr_p): curr_p = entry_price
             val = shares * curr_p
        
        equity_curve.append(val)
        
    # Return normalized series with HH:MM index
    # Normalize to % Return
    ret_series = [(x / initial_capital - 1.0) * 100 for x in equity_curve]
    
    # Create time-only index
    time_index = [t.strftime("%H:%M") for t in session_idx]
    
    return time_index, ret_series, (capital/initial_capital - 1.0)*100

def visualize_week_overlap():
    dates = ["2025-12-15", "2025-12-16", "2025-12-17", "2025-12-18", "2025-12-19"]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    plt.figure(figsize=(14, 8))
    
    has_data = False
    
    for i, d in enumerate(dates):
        print(f"Processing {d}...")
        res = simulate_day_pnl(d.replace("-", ""))
        if res:
            times, values, final_ret = res
            # Convert times to simplified x-axis for plotting?
            # matplotlib doesn't like string x-axis for many points easily without overlap.
            # Use dummy date for x-axis to overlay
            
            dummy_dates = [datetime.strptime(f"2000-01-01 {t}", "%Y-%m-%d %H:%M") for t in times]
            
            label = f"{d} ({final_ret:+.2f}%)"
            plt.plot(dummy_dates, values, label=label, color=colors[i], linewidth=2, alpha=0.8)
            has_data = True
            
            # Annotate End
            plt.text(dummy_dates[-1], values[-1], f" {final_ret:+.1f}%", color=colors[i], fontsize=9, fontweight='bold')
    
    if not has_data:
        print("No data found to plot.")
        return

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
    
    plt.title("Intraday Hero Strategy Performance: Week-1 Overlap", fontsize=16)
    plt.xlabel("Time (09:00 ~ 15:30)", fontsize=12)
    plt.ylabel("Return (%)", fontsize=12)
    plt.axhline(0, color='black', linestyle='--', linewidth=1)
    plt.legend(loc='upper left', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3)
    
    out_path = project_root / "results" / "reports" / "week_overlap_equity.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(out_path)
    print(f"Saved Overlap Chart: {out_path}")

if __name__ == "__main__":
    visualize_week_overlap()
