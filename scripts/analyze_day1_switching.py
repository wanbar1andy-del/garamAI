
import pandas as pd
import glob
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DATA_DIR = "GARAM_Data/day1_replay"
REPORT_DIR = "results/reports"

def analyze_race():
    print("Analyzing Day-1 Hero Race...")
    
    # 1. Load Data
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    dfs = {}
    
    for f in files:
        if "summary" in f: continue
        sym = os.path.basename(f).replace(".csv", "")
        # Read
        df = pd.read_csv(f, parse_dates=['ts'], index_col='ts')
        # Cleanup TZ if persists (should be clean now)
        # Cleanup TZ if persists (should be clean now)
        if df.index.tz is not None:
             df.index = df.index.tz_localize(None)
        
        # Shift to KST (UTC+9) if data is in UTC range (00~09)
        if df.index[0].hour < 8:
            df.index = df.index + pd.Timedelta(hours=9)
             
        # Filter: 9:00 ~ 15:30
        df = df.between_time("09:00", "15:30")
        if df.empty: continue
        
        # Calc Intraday Return (Cumulative)
        start_price = df['open'].iloc[0]
        df['return_pct'] = (df['close'] - start_price) / start_price * 100.0
        
        dfs[sym] = df['return_pct']
        
    # Combine into big DataFrame (Time x Sym)
    full_df = pd.DataFrame(dfs)
    # Forward Fill (for missing minutes)
    full_df = full_df.ffill().dropna(how='all')
    
    if full_df.empty:
        print("No data for analysis.")
        return

    # 2. Identify Top 5 at End of Day
    final_rets = full_df.iloc[-1].sort_values(ascending=False)
    top_5_syms = final_rets.head(5).index.tolist()
    print(f"Top 5 Final: {top_5_syms}")
    
    # 3. Plot "The Race" (Returns over Time)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Highlight 319400 if present
    hero = "319400"
    
    for sym in top_5_syms:
        style = '--' if sym != hero else '-'
        width = 3 if sym == hero else 1.5
        alpha = 1.0 if sym == hero else 0.7
        label = f"{sym} (Hero)" if sym == hero else sym
        
        ax.plot(full_df.index, full_df[sym], label=label, linestyle=style, linewidth=width, alpha=alpha)
        
    ax.set_title("Day-1 Hero Race: Intraday Return Comparison (2026-01-02)")
    ax.set_ylabel("Return (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    out_path = os.path.join(REPORT_DIR, "day1_hero_race.png")
    os.makedirs(REPORT_DIR, exist_ok=True)
    plt.savefig(out_path)
    print(f"Saved Race Chart: {out_path}")
    
    # 4. Analyze "Ranking Changes"
    # Rank table (1 = Best)
    rank_df = full_df.rank(axis=1, ascending=False)
    
    # Check 319400 Rank over time
    if hero in rank_df.columns:
        hero_rank = rank_df[hero]
        # Resample to 10min for readability
        hero_rank_10m = hero_rank.resample('10min').mean()
        
        print("\n=== Hero 319400 Rank Flow (1=Best) ===")
        print(hero_rank_10m.tail(10))
        
        # Did it drop out of Top 3 ever after 10:00?
        # Filter time > 10:00
        mask = hero_rank.index.time > pd.to_datetime("10:00").time()
        drops = hero_rank[mask][hero_rank[mask] > 3]
        if not drops.empty:
            print(f"\n[Warning] Hero dropped out of Top 3 for {len(drops)} minutes.")
        else:
            print(f"\n[Confirm] Hero stayed in Top 3 continuously after 10:00.")

if __name__ == "__main__":
    analyze_race()
