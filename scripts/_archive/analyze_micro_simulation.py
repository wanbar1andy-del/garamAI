import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Setup paths
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

# Period: The buildup to the crash and the crash itself
START_DATE = "2025-10-20"
END_DATE = "2025-11-24"

TARGETS = {
    "108490": "Loser #1 (Rank 1)",
    "030530": "Loser #2 (Rank 2)",
    "458870": "Winner (Rank 3)"
}

def calculate_indicators(df):
    # RSI 14
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MA 20 & Divergence
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['dist_ma20'] = (df['close'] - df['ma20']) / df['ma20'] * 100
    
    # Momentum 6m
    df['mom6m'] = df['close'].pct_change(periods=126)
    
    # Daily Return (Next Day Return for simulation)
    # Actually we trade at Close, so we realize Next Day's Close-to-Close return?
    # Or simplified: We hold from Today Close to Tomorrow Close.
    df['ret_1d'] = df['close'].pct_change().shift(-1) 
    
    return df

def run_micro_sim():
    print(f"--- MICRO SIMULATION: {START_DATE} to {END_DATE} ---")
    
    # Load Data
    full_data = {}
    for sym in TARGETS:
        daily_file = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        df = pd.read_csv(daily_file)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = calculate_indicators(df)
        full_data[sym] = df.loc[START_DATE:END_DATE]
        
    dates = sorted(list(set([d for sym in full_data for d in full_data[sym].index])))
    if not dates: return

    # Simulation State
    equity_blind = 100.0
    equity_smart = 100.0
    
    blind_holdings = []
    smart_holdings = []
    
    print(f"\n{'Date':<12} | {'Blind Pick (Rank 1)':<20} | {'Smart Pick (Filtered)':<20} | {'Blind Ret':<10} | {'Smart Ret':<10} | {'Blind Eq':<8} | {'Smart Eq':<8}")
    print("-" * 110)

    for d in dates[:-1]: # Stop before last day as we need next day return
        d_str = d.strftime("%m-%d")
        
        # 1. Gather Candidates for Today
        candidates = []
        for sym in TARGETS:
            if d in full_data[sym].index:
                row = full_data[sym].loc[d]
                candidates.append({
                    'sym': sym,
                    'mom': row['mom6m'],
                    'rsi': row['rsi'],
                    'dist': row['dist_ma20'],
                    'next_ret': row['ret_1d'] # Return realized tomorrow
                })
        
        if not candidates: continue
        
        # 2. Strategy A: Blind Momentum (Pick Highest Mom)
        candidates.sort(key=lambda x: x['mom'], reverse=True)
        blind_pick = candidates[0]
        
        # 3. Strategy B: Smart Momentum (Pick Highest Mom that is NOT Overheated)
        # Filter: RSI < 80 and MA Dist < 40
        smart_pick = None
        for c in candidates:
            # Check Filters
            is_overheated = (c['rsi'] > 80) or (c['dist'] > 40)
            if not is_overheated:
                smart_pick = c
                break
        
        # Fallback if all overheated (pick best of bad bunch? or Cash? Let's say Cash/No trade -> 0 return)
        # But here we assume we must pick one from this list? Or fallback to Blind if all same?
        # Let's say if smart_pick is None, we go to cash (0 return).
        
        # Calc Returns
        r_blind = blind_pick['next_ret']
        r_smart = smart_pick['next_ret'] if smart_pick else 0.0
        
        equity_blind *= (1 + r_blind)
        equity_smart *= (1 + r_smart)
        
        # Logging
        b_desc = f"{blind_pick['sym']} ({blind_pick['mom']*100:.0f}%)"
        if smart_pick:
             s_desc = f"{smart_pick['sym']} ({smart_pick['mom']*100:.0f}%, R:{smart_pick['rsi']:.0f})"
        else:
             s_desc = "CASH (All Overheat)"
             
        # Highlight Divergence
        note = ""
        if blind_pick['sym'] != (smart_pick['sym'] if smart_pick else 'None'):
            note = " <== SWITCH"
            
        print(f"{d_str:<12} | {b_desc:<20} | {s_desc:<20} | {r_blind*100:>8.2f}% | {r_smart*100:>8.2f}% | {equity_blind:>8.1f} | {equity_smart:>8.1f}{note}")

    print("-" * 110)
    print(f"Final Result:")
    print(f"Blind Momentum Equity: {equity_blind:.2f} ({(equity_blind-100):.2f}%)")
    print(f"Smart Momentum Equity: {equity_smart:.2f} ({(equity_smart-100):.2f}%)")
    
    if equity_smart > equity_blind:
        print(f"Improvement: +{equity_smart - equity_blind:.2f} points")

run_micro_sim()
