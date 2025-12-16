import sys
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS
from garam.core.alpha_aggregator import AlphaAggregator

def debug_aggregator():
    print("--- Debugging AlphaAggregator ---")
    
    # Load 1 Stock Data
    sym = "005930" # Samsung Electronics (Likely in universe)
    # Check if target available in Top 50
    uni = pd.read_csv(PATHS.DATA_DIR / "real_universe_400.csv")
    targets = uni['Code'].astype(str).str.zfill(6).tolist()[:50]
    sym = targets[0]
    print(f"Target: {sym}")
    
    f = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
    if not f.exists():
        print(f"File not found: {f}")
        return

    df = pd.read_csv(f)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Create Market Data
    md = {
        'close': pd.DataFrame({sym: df['close']}),
        'open': pd.DataFrame({sym: df['open']}),
        'high': pd.DataFrame({sym: df['high']}),
        'low': pd.DataFrame({sym: df['low']}),
        'volume': pd.DataFrame({sym: df['volume']})
    }
    
    agg = AlphaAggregator()
    print(f"Loaded {len(agg.alphas)} alphas.")
    
    regime = 'R3_UP_BOX'
    
    # Run Compute
    try:
        final, raw = agg.compute_final_score(md, [sym], regime)
        print("Final Scores DF:")
        print(final.tail())
        
        if final.empty:
            print("Final Scores FAIL (Empty)")
        else:
            print("Final Scores PASS")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_aggregator()
