import pandas as pd
import numpy as np
import sys
from pathlib import Path
from run_alpha_robust import load_data

def detect_whales():
    print("::: GARAM WHALE FORENSIC ANALYSIS :::")
    print("Scanning for: Accumulation (Coiling), Strikes (Explosion), Distribution (Dumps)")
    
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    closes, volumes = load_data(data_dir, "universe.csv", "20250601", "20251212")
    
    whale_events = []
    
    print(f"[Whale] Scanned Universe: {len(closes.columns)} symbols")
    
    for sym in closes.columns:
        c = closes[sym].dropna()
        v = volumes[sym].reindex(c.index).fillna(0)
        
        if c.empty: continue
        
        # 1. Calculate Indicators
        # Volatility (BB Width)
        rolling = c.rolling(window=20)
        mid = rolling.mean()
        std = rolling.std()
        bb_width = (mid + 2*std - (mid - 2*std)) / (mid + 1e-9)
        
        # Volume Intensity
        v_ma20 = v.rolling(window=20).mean()
        vol_ratio = v / (v_ma20 + 1e-9)
        
        # 2. Detect Patterns
        # A. The Coil (Accumulation): BB Width < 0.005 (0.5%) for > 1 hour (60 mins)
        is_tight = (bb_width < 0.005)
        tight_run = is_tight.astype(int).groupby(is_tight.ne(is_tight.shift()).cumsum()).cumsum()
        
        # B. The Strike (Explosion): Vol > 5x AND Price > 1.5% in 1 min
        ret = c.pct_change()
        is_strike = (vol_ratio > 5.0) & (ret > 0.015)
        
        # C. The Dump (Distribution): Vol > 5x AND PriceStall (Abs(Ret) < 0.2%) OR Reversal (High wick)
        # Simplified: Huge Vol, Small Move = Climax/Churning
        is_climax = (vol_ratio > 5.0) & (ret.abs() < 0.002)
        
        # 3. Log Events
        # Find Strikes
        strike_indices = is_strike[is_strike].index
        for ts in strike_indices:
            # Check if preceded by Coil
            loc = c.index.get_loc(ts)
            if loc < 60: continue
            
            # Look back 60 mins for coil
            pre_coil_score = is_tight.iloc[loc-60:loc].mean()
            
            if pre_coil_score > 0.7: # 70% of last hour was tight
                whale_events.append({
                    "type": "STRIKE (Accumulation -> Breakout)",
                    "sym": sym,
                    "ts": ts,
                    "magnitude": f"Vol {vol_ratio.loc[ts]:.1f}x, Price +{ret.loc[ts]*100:.1f}%",
                    "context": f"Coiled for {pre_coil_score*60:.0f} mins"
                })
                
        # Find Dumps
        dump_indices = is_climax[is_climax].index
        for ts in dump_indices:
            # Check RSI
            # Calculate simple RSI on the fly
            window_ret = ret.iloc[c.index.get_loc(ts)-14 : c.index.get_loc(ts)]
            if len(window_ret) < 14: continue
            
            gain = window_ret[window_ret>0].mean()
            loss = -window_ret[window_ret<0].mean()
            if np.isnan(gain): gain=0
            if np.isnan(loss): loss=1
            rsi = 100 - 100/(1 + gain/loss) if loss > 0 else 100
            
            if rsi > 75:
                whale_events.append({
                    "type": "DUMP (Distribution Climax)",
                    "sym": sym,
                    "ts": ts,
                    "magnitude": f"Vol {vol_ratio.loc[ts]:.1f}x, Price Stalled",
                    "context": f"RSI {rsi:.0f} (Overheated)"
                })
    
    # Report
    print(f"\n[Whale Report] Detected {len(whale_events)} Significant Movements")
    df_ev = pd.DataFrame(whale_events)
    
    if not df_ev.empty:
        print("\n=== TOP 10 WHALE MOVEMENTS ===")
        # Sort by Type then Timestamp
        df_ev = df_ev.sort_values(by="ts", ascending=False)
        print(df_ev.head(10).to_string(index=False))
        
        print("\n=== PATTERN SUMMARY ===")
        print(df_ev['type'].value_counts())
        
        # Detailed Analysis of Top 1
        top_event = df_ev.iloc[0]
        print(f"\n[Deep Dive: {top_event['sym']} at {top_event['ts']}]")
        print(f"Action: {top_event['type']}")
        print(f"Details: {top_event['magnitude']}")
        print(f"Background: {top_event['context']}")
        print("Interpretation: 'Smart Money' executed a synchronized move.")
        
    else:
        print("No extreme whale footprints found in this sample.")

if __name__ == "__main__":
    detect_whales()
