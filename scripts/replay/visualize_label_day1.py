import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def visualize_day(target_date_str="20251217"):
    target_date = pd.to_datetime(target_date_str)
    day_dir = project_root / "results" / "labels" / f"day={target_date_str}"
    seg_path = day_dir / "hero_segments.csv"
    
    if not seg_path.exists():
        print(f"No segments found for {target_date_str}")
        return

    # Load Segments
    df_seg = pd.read_csv(seg_path)
    df_seg['start_time'] = pd.to_datetime(df_seg['start_time'])
    df_seg['end_time'] = pd.to_datetime(df_seg['end_time'])
    
    # Filter Top-Rank Segments (Rank 1 only for clear visualization)
    # We want to form a continuous chain of "Best Opportunities"
    # Sort by start time
    df_seg.sort_values('start_time', inplace=True)
    
    # Simulation Settings
    initial_capital = 10_000_000.0
    capital = initial_capital
    cost_rate = 0.0010 # 10bps
    
    equity_curve = [] # [(time, equity)]
    trades = []
    
    # Market Data (Proxy: 005930 or Universe Index if saved. Using 005930 for now)
    market_path = project_root / "GARAM_Data" / "history" / "minute" / "005930.csv"
    df_mkt = pd.read_csv(market_path, usecols=['date', 'close'])
    try:
        df_mkt['date'] = pd.to_datetime(df_mkt['date'].astype(str), format='%Y%m%d%H%M%S')
    except:
        df_mkt['date'] = pd.to_datetime(df_mkt['date'])
        
    df_mkt = df_mkt[df_mkt['date'].dt.date == target_date.date()].sort_values('date')
    if df_mkt.empty:
        print("Market data missing")
        return
        
    market_curve = df_mkt.set_index('date')['close']
    market_curve = market_curve / market_curve.iloc[0] * initial_capital # Normalize to Capital
    
    # Replay Loop (Minute by Minute)
    # Simple Logic: If inside a Rank 1 Segment, hold it. Else Cash.
    # Handling Overlaps: Prioritize higher segment score or just first one?
    # Let's take 'Best Segment' active at any time.
    
    # 1. Expand Segments to Minute Index
    session_idx = pd.date_range(f"{target_date_str} 09:00", f"{target_date_str} 15:30", freq="1T")
    
    current_holding = None # symbol
    entry_price = 0.0
    shares = 0
    
    # Pre-load prices for relevant symbols
    active_symbols = df_seg['symbol'].unique()
    price_cache = {}
    for sym in active_symbols:
        p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
        if p.exists():
            d = pd.read_csv(p, usecols=['date', 'close'])
            try:
                d['date'] = pd.to_datetime(d['date'].astype(str), format='%Y%m%d%H%M%S')
            except:
                d['date'] = pd.to_datetime(d['date'])
            d = d[d['date'].dt.date == target_date.date()].set_index('date')['close']
            price_cache[sym] = d
    
    equity_ts = []
    
    # Identify "Target Symbol" for each minute
    # Priority: Inside a valid segment, Highest Segment Score
    target_timeline = pd.Series(index=session_idx, dtype=object)
    
    for _, seg in df_seg.iterrows():
        # Only use segments with positive total_net_rel_ret?
        # User said "Hero Label". We use all output segments (assumed labeled correctly)
        rng = pd.date_range(seg['start_time'], seg['end_time'], freq="1T")
        for t in rng:
            if t in target_timeline.index:
                # If overlap, overwrite if score is higher (Simplified greedy)
                current = target_timeline.loc[t]
                if pd.isna(current):
                    target_timeline.loc[t] = seg['symbol']
                # Complexity: Switching costs. 
                # Let's stick to: Enter Segment, Hold until End. Ignore overlap starts?
                # Simpler: Just plotting the segment performance.
    
    # Strict Simulation
    for t in session_idx:
        # Check Exits
        if current_holding:
            # Are we still in a valid segment for this holding?
            # Or did the segment end?
            # Look up segment end time
            # Simplify: If target_timeline[t] != current_holding, Sell.
            target = target_timeline.get(t)
            if target != current_holding:
                # SELL
                price_series = price_cache.get(current_holding)
                if price_series is not None and t in price_series.index:
                    exit_price = price_series.loc[t]
                else: 
                     # Fallback to previous close
                     prev_t = t - pd.Timedelta(minutes=1)
                     exit_price = price_series.asof(t) if price_series is not None else entry_price

                # Execute Sell
                gross = shares * exit_price
                capital = gross * (1 - cost_rate/2) # Exit Cost
                trades.append({'time': t, 'type': 'SELL', 'symbol': current_holding, 'price': exit_price, 'cap': capital})
                current_holding = None
                shares = 0
        
        # Check Entries
        if not current_holding:
            target = target_timeline.get(t)
            if isinstance(target, str) or isinstance(target, int): # Valid symbol
                target = str(target).zfill(6)
                price_series = price_cache.get(target)
                if price_series is not None:
                     current_price = price_series.asof(t)
                     if pd.notna(current_price) and current_price > 0:
                         # BUY
                         cost_amt = capital * (cost_rate/2) # Entry cost
                         net_cap = capital - cost_amt
                         shares = net_cap / current_price
                         entry_price = current_price
                         current_holding = target
                         trades.append({'time': t, 'type': 'BUY', 'symbol': target, 'price': entry_price, 'cap': capital})

        # MTM
        if current_holding:
             price_series = price_cache.get(current_holding)
             curr_p = price_series.asof(t) if price_series is not None else entry_price
             if pd.isna(curr_p): curr_p = entry_price
             val = shares * curr_p
             equity_ts.append(val)
        else:
             equity_ts.append(capital)

    # Plot
    df_eq = pd.DataFrame({'equity': equity_ts}, index=session_idx)
    
    plt.figure(figsize=(12, 6))
    
    # 1. Equity
    plt.plot(df_eq.index, df_eq['equity'], label='Hero Strategy (100% Comp)', color='red', linewidth=2)
    
    # 2. Market (Normalized)
    plt.plot(market_curve.index, market_curve, label='KOSPI Proxy (005930)', color='gray', linestyle='--', alpha=0.7)

    # 3. Trade Markers
    for tr in trades:
        if tr['type'] == 'BUY':
            plt.scatter(tr['time'], tr['cap'], marker='^', color='green', s=50)
        else:
            plt.scatter(tr['time'], tr['cap'], marker='v', color='blue', s=50)

    final_ret = (df_eq['equity'].iloc[-1] / initial_capital) - 1.0
    plt.title(f"Day-1 Replay ({target_date_str}): Return {final_ret*100:.2f}% | Trades: {len(trades)//2}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    out_path = day_dir / "equity_curve.png"
    plt.savefig(out_path)
    print(f"Saved Chart: {out_path}")
    print(f"Final Return: {final_ret*100:.2f}%")
    print(f"Trade Count: {len(trades)//2}")

if __name__ == "__main__":
    visualize_day("20251217")
