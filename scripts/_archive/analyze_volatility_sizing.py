import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

START_DATE = "2025-10-20"
END_DATE = "2025-11-24"

TARGETS = {
    "108490": "Loser 1",
    "030530": "Loser 2",
    "458870": "Winner"
}

def run_vol_sim():
    print(f"--- VOLATILITY SIZING SIMULATION ({START_DATE} ~ {END_DATE}) ---")
    
    data = {}
    for sym in TARGETS:
        f = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        df = pd.read_csv(f)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        # Calculate ATR(14) %
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        df['atr_pct'] = (atr / df['close']) * 100
        data[sym] = df.loc[START_DATE:END_DATE]

    # Pre-Crash Snapshot (e.g. Nov 1) to determine allocation
    # We want to see allocation *before* the crash.
    dates = sorted(list(data["108490"].index)) 
    check_date = pd.Timestamp("2025-11-03")
    
    print(f"\n[Allocation Check at {check_date.date()}]")
    print(f"{'Symbol':<10} | {'ATR % (Risk)':<12} | {'Score Weight (Old)':<18} | {'Vol Weight (New)':<18}")
    print("-" * 70)
    
    # 1. Score Weight (Simulated based on previous Rank findings)
    # Rank 1 (108490) ~ Score 700 -> Weight ~40%
    # Rank 2 (030530) ~ Score 600 -> Weight ~30%
    # Rank 3 (458870) ~ Score 500 -> Weight ~20%
    # (Simplified for top 3 normalization)
    
    # 2. Vol Weight = 1 / ATR
    inv_atrs = {}
    total_inv_atr = 0
    
    row_data = []

    for sym in TARGETS:
        if check_date in data[sym].index:
            atr = data[sym].loc[check_date]['atr_pct']
            inv_atr = 1 / atr if atr > 0 else 0
            inv_atrs[sym] = inv_atr
            total_inv_atr += inv_atr
            row_data.append({'sym': sym, 'atr': atr, 'inv_atr': inv_atr})
            
    # Calculate Weights
    total_capital = 10000.0 # $10k
    
    # Hypothetical Score Weights (from Momentum Logic)
    # High Mom -> High Weight
    score_weights = {
        "108490": 0.45, # Rank 1 (Loser)
        "030530": 0.35, # Rank 2 (Loser)
        "458870": 0.20  # Rank 3 (Winner)
    }
    
    # Volatility Weights
    vol_weights = {}
    for r in row_data:
        w = r['inv_atr'] / total_inv_atr
        vol_weights[r['sym']] = w
        
    for r in row_data:
        sym = r['sym']
        sw = score_weights.get(sym, 0.0)
        vw = vol_weights.get(sym, 0.0)
        print(f"{sym:<10} | {r['atr']:>8.2f}%    | {sw*100:>8.1f}%           | {vw*100:>8.1f}%")
        
    print("-" * 70)
    
    # Performance Simulation
    print("\n--- PERFORMANCE RESULT (Nov 3 - Nov 24) ---")
    
    # Calculate Return of each stock
    stock_returns = {}
    for sym in TARGETS:
        start_p = data[sym].loc[check_date]['close']
        end_p = data[sym].iloc[-1]['close'] # Nov 24
        ret = (end_p - start_p) / start_p
        stock_returns[sym] = ret
        
    # Portfolio Return
    def calc_port_ret(weights):
        ret = 0
        for sym, w in weights.items():
            ret += w * stock_returns.get(sym, 0)
        return ret
        
    ret_score = calc_port_ret(score_weights)
    ret_vol = calc_port_ret(vol_weights)
    
    print(f"Score Weighted Return (Mom): {ret_score*100:.2f}%")
    print(f"Volatility Weighted Return : {ret_vol*100:.2f}%")
    
    diff = ret_vol - ret_score
    print(f"Improvement: {diff*100:+.2f}% points")
    
    print("\n--- CONCLUSION ---")
    if diff > 0:
        print("Volatility Sizing worked! By allocating less to the risky/volatile assets")
        print("(Losers) and more to the steady Winner, we reduced losses significantly.")
    else:
        print("Volatility Sizing failed. The Winner was actually more volatile?")

run_vol_sim()
