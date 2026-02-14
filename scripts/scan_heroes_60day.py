
import pandas as pd
import glob
import os

DATA_DIR = "GARAM_Data/60day_replay_kst"
HERO_THRESHOLD = 0.10 # +10% Intraday Rise

def scan_heroes():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    print(f"Scanning {len(files)} symbols for >{HERO_THRESHOLD*100:.0f}% Intraday Heroes...")

    hero_counts = {} # Date -> Count
    hero_symbols = {} # Date -> List of Symbols

    for f in files:
        try:
            df = pd.read_csv(f, parse_dates=['ts'])
            if df.empty: continue
            
            df['date'] = df['ts'].dt.date
            
            # Group by date
            daily = df.groupby('date').agg({
                'open': 'first',
                'high': 'max'
            })
            
            daily['rise'] = (daily['high'] - daily['open']) / daily['open']
            
            heroes = daily[daily['rise'] > HERO_THRESHOLD]
            
            for date_val, row in heroes.iterrows():
                d_str = str(date_val)
                hero_counts[d_str] = hero_counts.get(d_str, 0) + 1
                if d_str not in hero_symbols: hero_symbols[d_str] = []
                # Record Symbol and Rise
                sym = os.path.basename(f).replace(".csv","")
                hero_symbols[d_str].append(f"{sym}({row['rise']*100:.1f}%)")
                
        except: pass

    # Sort by date
    sorted_dates = sorted(hero_counts.keys())
    
    print("\n--- Hero Scan Report (Threshold > +10%) ---")
    total_heroes = 0
    for d in sorted_dates:
        cnt = hero_counts[d]
        syms = hero_symbols[d]
        total_heroes += cnt
        # Show top 5 symbols
        display_syms = ", ".join(syms[:5])
        if len(syms) > 5: display_syms += f", ... (+{len(syms)-5} more)"
        print(f"{d}: {cnt} Heroes -> {display_syms}")

    print(f"\nTotal Heroes detected in 60 days: {total_heroes}")
    if len(sorted_dates) > 0:
        print(f"Average Heroes per Day: {total_heroes / len(sorted_dates):.1f}")

if __name__ == "__main__":
    scan_heroes()
