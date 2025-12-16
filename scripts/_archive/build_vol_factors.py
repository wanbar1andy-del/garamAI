import sys
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import multiprocessing

# Add project root to path
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS
from garam.engine.volatility_engine import VolatilityFactorEngine

def process_single_stock(args):
    """
    Process a single stock to generate volatility factors.
    Args: (symbol, input_path, output_dir)
    """
    symbol, input_path, output_dir = args
    
    try:
        if not input_path.exists():
            return (symbol, False, "File not found")
        
        df = pd.read_csv(input_path)
        # Ensure standard columns
        df.columns = [c.lower() for c in df.columns]
        
        if 'date' not in df.columns:
            return (symbol, False, "No date column")
            
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate Factors
        enriched_df = VolatilityFactorEngine.calculate_factors(df)
        
        # Save enriched daily data
        output_file = output_dir / f"{symbol}_volf.csv"
        enriched_df.to_csv(output_file)
        
        # Return last row for snapshot
        last_row = enriched_df.iloc[-1].to_dict()
        last_row['symbol'] = symbol
        last_row['date'] = enriched_df.index[-1]
        
        # Add Status
        last_row['signal_status'] = VolatilityFactorEngine.get_signal_status(last_row)
        
        return (symbol, True, last_row)
        
    except Exception as e:
        return (symbol, False, str(e))

def factor_builder():
    print("--- Volatility Factor Builder ---")
    
    # 1. Setup Output Directory
    # We will store factor files in GARAM_Data/factors
    factor_dir = PATHS.DATA_DIR / "factors"
    factor_dir.mkdir(exist_ok=True)
    
    # 2. Load Universe
    uni_path = PATHS.DATA_DIR / "real_universe_400.csv"
    if not uni_path.exists():
        print("Universe file not found!")
        return
        
    uni_df = pd.read_csv(uni_path)
    # Handle 'Code' or 'symbol'
    if 'Code' in uni_df.columns:
        symbols = uni_df['Code'].astype(str).str.zfill(6).tolist()
    else:
        symbols = uni_df['symbol'].astype(str).str.zfill(6).tolist()
        
    print(f"Processing {len(symbols)} symbols...")
    
    # 3. Prepare Args for Parallel Processing
    tasks = []
    for sym in symbols:
        input_path = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        tasks.append((sym, input_path, factor_dir))
        
    # 4. Run Parallel
    # Windows multiprocessing can be tricky, stick to simple loop if uncertain or use simple Pool
    # We'll use a simple loop for safety/debuggability first, speed is secondary (400 files is fast)
    results = []
    snapshot_data = []
    
    for task in tqdm(tasks, desc="Calculating Factors"):
        sym, success, data = process_single_stock(task)
        if success:
            snapshot_data.append(data)
        else:
            # print(f"Failed {sym}: {data}")
            pass
            
    # 5. Create Snapshot Report
    if snapshot_data:
        snap_df = pd.DataFrame(snapshot_data)
        snap_path = PATHS.DATA_DIR / "volatility_snapshot_latest.csv"
        snap_df.to_csv(snap_path, index=False)
        print(f"\nSnapshot saved to: {snap_path}")
        print(f"Daily Factor files saved to: {factor_dir}")
        print("-" * 50)
        print("Top 5 Highest Risk (ATR%):")
        print(snap_df.sort_values('atr_pct', ascending=False)[['symbol', 'atr_pct', 'vol_accel']].head(5))
        print("\nTop 5 Highest Quality (Quality Score):")
        print(snap_df.sort_values('quality_score', ascending=False)[['symbol', 'quality_score', 'ret_6m', 'atr_pct']].head(5))
        print("\nTop 5 Crash Warnings (Vol Accel):")
        print(snap_df.sort_values('vol_accel', ascending=False)[['symbol', 'vol_accel', 'signal_status']].head(5))

if __name__ == "__main__":
    factor_builder()
