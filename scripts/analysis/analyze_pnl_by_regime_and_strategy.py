import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS

def load_regime_lookup():
    print("Loading Regime Data...")
    lookup = {}
    regime_dir = PATHS.BASE_DIR / "analysis/regimes"
    
    for file_path in regime_dir.glob("intraday_with_regime_*.csv"):
        symbol = file_path.stem.split('_')[-1] # intraday_with_regime_005930.csv -> 005930
        
        # Read only necessary columns
        # We need date and regime_id
        # The file is 1m data, so it's large.
        # But regime_id is constant per day.
        # So we can just read unique date/regime pairs.
        
        # Optimization: Read chunks or just read specific columns if possible.
        # pd.read_csv supports usecols.
        # Columns: timestamp, ..., date_only, regime_id
        
        try:
            df = pd.read_csv(file_path, usecols=['date_only', 'regime_id'])
            df['date_only'] = pd.to_datetime(df['date_only'])
            
            # Drop duplicates to get daily regime
            daily_regimes = df.drop_duplicates(subset=['date_only'])
            
            lookup[symbol] = daily_regimes.set_index('date_only')['regime_id'].to_dict()
            
        except Exception as e:
            print(f"Error loading {symbol}: {e}")
            
    return lookup

def analyze_performance():
    # strategies = ["Pure_v2", "Pure_v3"]
    # Dynamic discovery
    results_dir = PATHS.BASE_DIR / "results"
    strategies = [d.name for d in results_dir.iterdir() if d.is_dir() and (d / "trades.csv").exists()]
    print(f"Found strategies: {strategies}")
    all_trades = []
    
    # 1. Load Regime Lookup
    regime_lookup = load_regime_lookup()
    
    # 2. Load Trades and Tag Regime
    for strategy in strategies:
        trades_file = PATHS.BASE_DIR / "results" / strategy / "trades.csv"
        if not trades_file.exists():
            print(f"Warning: No trades for {strategy}")
            continue
            
        trades = pd.read_csv(trades_file)
        trades['entry_time'] = pd.to_datetime(trades['entry_time'])
        trades['date_only'] = trades['entry_time'].dt.date
        trades['date_only'] = pd.to_datetime(trades['date_only'])
        
        print(f"Processing {len(trades)} trades for {strategy}...")
        
        for idx, row in trades.iterrows():
            symbol = str(row.get('symbol', 'UNKNOWN'))
            date = row['date_only']
            
            regime = "UNKNOWN"
            if symbol in regime_lookup and date in regime_lookup[symbol]:
                regime = regime_lookup[symbol][date]
                
            trades.at[idx, 'regime_id'] = regime
            trades.at[idx, 'strategy'] = strategy
            
        all_trades.append(trades)
        
    if not all_trades:
        print("No trades found.")
        return
        
    merged_trades = pd.concat(all_trades)
    
    # 3. Aggregate PnL by Regime & Strategy
    # Group by [regime_id, strategy]
    # Use return_r for avg_R and win_rate calculation
    summary = merged_trades.groupby(['regime_id', 'strategy']).apply(
        lambda x: pd.Series({
            'trades': len(x),
            'total_pnl': x['pnl'].sum(),
            'avg_R': x['return_r'].mean(),
            'win_rate': (x['pnl'] > 0).mean()
        })
    )
    
    print("\n=== PnL by Regime & Strategy ===")
    print(summary)
    
    # Save to CSV
    output_file = PATHS.BASE_DIR / "results" / "pnl_by_regime_strategy.csv"
    summary.to_csv(output_file)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    analyze_performance()
