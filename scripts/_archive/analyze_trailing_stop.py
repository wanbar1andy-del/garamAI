import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

START_DATE = "2025-10-20"
END_DATE = "2025-11-24"

TARGETS = {
    "458870": "Winner"
}

def run_stop_loss_sim():
    print(f"--- TRAILING STOP SIMULATION ({START_DATE} ~ {END_DATE}) ---")
    
    # Load Universe for Names
    try:
        uni = pd.read_csv(PATHS.DATA_DIR / "real_universe_400.csv", dtype={'Code': str})
        uni.set_index('Code', inplace=True)
    except:
        uni = pd.DataFrame()

    for sym, label in TARGETS.items():
        name = uni.loc[sym, 'Name'] if sym in uni.index else sym
        print(f"\nAnalyzing {sym} ({name}) - {label}")
        
        daily_file = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        if not daily_file.exists(): continue
        
        df = pd.read_csv(daily_file)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        period = df.loc[START_DATE:END_DATE]
        
        if period.empty: continue
        
        # Sim Logic
        # Buy on Start Date
        entry_price = period.iloc[0]['close']
        high_water_mark = entry_price
        
        stop_triggered = False
        exit_price = 0
        exit_date = None
        
        # Trailing Stop Thresholds to Test
        thresholds = [0.03, 0.05, 0.07, 0.10] # 3%, 5%, 7%, 10%
        
        print(f"Entry: {period.index[0].date()} @ {entry_price}")
        
        peak_price = period['close'].max()
        final_price = period.iloc[-1]['close']
        max_dd_hold = (final_price - peak_price) / peak_price
        
        print(f"Buy & Hold Return: {(final_price/entry_price - 1)*100:.2f}%")
        print(f"Max Drawdown (Price): {max_dd_hold*100:.2f}%")
        
        print("-" * 60)
        print(f"{'Stop %':<10} | {'Exit Date':<12} | {'Exit Price':<10} | {'Return':<10} | {'Saved %':<10}")
        print("-" * 60)

        for ts in thresholds:
            hw = entry_price
            triggered = False
            e_price = 0
            e_date = None
            
            for date, row in period.iterrows():
                price = row['close']
                if price > hw:
                    hw = price
                
                # Check Stop (at Close)
                stop_price = hw * (1 - ts)
                if price < stop_price:
                    triggered = True
                    e_price = price
                    e_date = date
                    break
            
            if triggered:
                ret = (e_price / entry_price - 1)
                saved = (e_price - final_price) / final_price # How much lower is the final?
                # Actually Saved Loss = (Exit Return) - (Hold Return)
                saved_loss = ret - (final_price/entry_price - 1)
                print(f"{ts*100:>2.0f}%        | {e_date.date()}   | {e_price:<10} | {ret*100:>8.2f}% | {saved_loss*100:>8.2f}%")
            else:
                print(f"{ts*100:>2.0f}%        | {'Top Not Hit':<12} | {'-':<10} | {'-':<10} | {'-':<10}")

run_stop_loss_sim()
