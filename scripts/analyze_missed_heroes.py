
import pandas as pd
import glob
import os

DATA_DIR = "GARAM_Data/5day_replay"
DATES = ['2025-12-09', '2025-12-10', '2025-12-11', '2025-12-12']

def analyze_missed():
    print("Scanning for Real Heroes (Dec 09-12)...")
    
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    daily_stats = {d: [] for d in DATES}
    
    for f in files:
        sym = os.path.basename(f).replace(".csv", "")
        try:
            df = pd.read_csv(f, parse_dates=['ts'])
            
            for d_str in DATES:
                target_date = pd.to_datetime(d_str).date()
                day_df = df[df['ts'].dt.date == target_date]
                
                if len(day_df) < 30: continue
                
                # Calc Stats
                open_p = day_df.iloc[0]['open']
                close_p = day_df.iloc[-1]['close']
                ret = (close_p - open_p) / open_p * 100.0
                
                # Volume Sum
                vol = day_df['volume'].sum()
                
                daily_stats[d_str].append({
                    'symbol': sym,
                    'return': ret,
                    'volume': vol,
                    'open': open_p,
                    'close': close_p
                })
                
        except Exception as e:
            continue

    # Report Top 3 per day
    for d_str in DATES:
        stats = daily_stats[d_str]
        if not stats:
            print(f"\n[{d_str}] No data found.")
            continue
            
        # Sort by Return
        stats.sort(key=lambda x: x['return'], reverse=True)
        top3 = stats[:3]
        
        print(f"\n[{d_str}] Market Top 3 Performers:")
        for rank, s in enumerate(top3, 1):
            print(f"  #{rank} {s['symbol']}: {s['return']:.2f}% (Vol: {s['volume']:,})")
            
        # Check if they are viable (e.g. Volume < 100k?)
        # If best stock has volume 100, it's garbage.

if __name__ == "__main__":
    analyze_missed()
