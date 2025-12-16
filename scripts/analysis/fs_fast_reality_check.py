"""
fs_fast Reality Check
Analyzes the predictive power of fs_fast signal across the available universe.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from garam.signals.utils import FsFastParams
from garam.signals.fs_fast import compute_fs_fast

def load_intraday_data(symbol: str) -> pd.DataFrame:
    """Load 1m intraday data"""
    path = PATHS.DATA_DIR / "kr" / "intraday" / "1m" / f"{symbol}_1m.csv"
    if not path.exists():
        return None
        
    df = pd.read_csv(path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
    return df

def analyze_symbol(symbol: str, params: FsFastParams):
    """Compute fs_fast and future returns for a symbol"""
    df = load_intraday_data(symbol)
    if df is None:
        return None
        
    # Compute fs_fast
    fs = compute_fs_fast(df, params)
    df['fs_fast'] = fs
    
    # Future returns (1h = 60 bars, EOD)
    # 1h return
    df['ret_1h'] = df['close'].shift(-60) / df['close'] - 1
    
    # EOD return (approximate, hard to do exactly without daily boundaries in simple script)
    # Let's just use 4h (240 bars) as proxy for "rest of day" or significant move
    df['ret_4h'] = df['close'].shift(-240) / df['close'] - 1
    
    return df[['fs_fast', 'ret_1h', 'ret_4h']].dropna()

def main():
    universe = [
        "000270", "000660", "005380", "005490", "005930", 
        "006400", "035420", "051910", "068270", "105560"
    ]
    
    print(f"Analyzing universe: {len(universe)} symbols")
    
    params = FsFastParams()
    all_data = []
    
    for symbol in universe:
        print(f"Processing {symbol}...")
        res = analyze_symbol(symbol, params)
        if res is not None:
            res['symbol'] = symbol
            all_data.append(res)
            
    if not all_data:
        print("No data found.")
        return
        
    full_df = pd.concat(all_data)
    
    # Binning
    bins = [-3.1, -1.5, -0.5, 0.5, 1.5, 3.1]
    labels = ["[-3,-1.5)", "[-1.5,-0.5)", "[-0.5,0.5)", "[0.5,1.5)", "[1.5,3]"]
    full_df["fs_fast_bin"] = pd.cut(full_df["fs_fast"], bins=bins, labels=labels)
    
    print("\n=== fs_fast Reality Check (1h Forward Return) ===")
    summary = full_df.groupby("fs_fast_bin")['ret_1h'].agg(
        n='count',
        avg_ret=lambda x: x.mean() * 100,
        win_rate=lambda x: (x > 0).mean() * 100,
        avg_pos=lambda x: x[x > 0].mean() * 100 if (x > 0).any() else np.nan,
        avg_neg=lambda x: x[x < 0].mean() * 100 if (x < 0).any() else np.nan
    )
    print(summary)
    
    print("\n=== fs_fast Reality Check (4h Forward Return) ===")
    summary_4h = full_df.groupby("fs_fast_bin")['ret_4h'].agg(
        n='count',
        avg_ret=lambda x: x.mean() * 100,
        win_rate=lambda x: (x > 0).mean() * 100
    )
    print(summary_4h)
    
    # Save to CSV for detailed analysis
    output_path = PATHS.EXPERIMENTS_DIR / "fs_fast_analysis.csv"
    full_df.to_csv(output_path)
    print(f"\nDetailed data saved to {output_path}")

if __name__ == "__main__":
    main()
