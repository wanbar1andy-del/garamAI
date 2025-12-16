import pandas as pd
import numpy as np
from pathlib import Path

def analyze_results():
    # 1. Load Results
    res_path = Path('hero_verification_results.csv')
    if not res_path.exists():
        print("No results found.")
        return

    df_res = pd.read_csv(res_path)
    df_res['time'] = pd.to_datetime(df_res['time'])
    
    # Filter for Rank 1 only
    heroes = df_res[df_res['rank'] == 1].copy()
    unique_symbols = heroes['symbol'].unique()
    
    print(f"Analyzing {len(heroes)} picks across {len(unique_symbols)} unique heroes...")
    
    # 2. Load Market Data for Heroes
    market_data = {}
    data_dir = Path("garamdata/history/minute")
    
    print("Loading hero price data...")
    for i, sym in enumerate(unique_symbols):
        s_code = str(sym).zfill(6)
        print(f"Loading [{i+1}/{len(unique_symbols)}] {s_code}...")
        try:
            # Try exact match first
            fpath = list(data_dir.glob(f"{s_code}_1m.csv"))
            if not fpath:
                fpath = list(data_dir.glob(f"{s_code}*_1m.csv"))
                
            if not fpath:
                print(f"File not found for {s_code}")
                continue
                
            # Robust Load Logic
            df = pd.read_csv(fpath[0])
            
            # ... parsing logic (truncated for brevity, keep existing) ...
            k_map = {'체결시간': 'date_kr', '현재가': 'close_kr'}
            df.rename(columns=k_map, inplace=True)
            
            # Coalesce
            if 'date_kr' in df.columns:
                if 'date' not in df.columns: df['date'] = df['date_kr']
                else: df['date'] = df['date'].fillna(df['date_kr'])
                
            if 'close_kr' in df.columns:
                if 'close' not in df.columns: df['close'] = df['close_kr']
                else: df['close'] = df['close'].fillna(df['close_kr'])
            
            if df['close'].dtype == object:
                df['close'] = df['close'].astype(str).str.replace('+', '').str.replace('-', '').astype(float)
            df['close'] = df['close'].abs()
            
            raw_date = df['date'].copy()
            numeric_dates = pd.to_numeric(raw_date, errors='coerce')
            mask_num = numeric_dates.notna()
            if mask_num.any():
                df.loc[mask_num, 'date'] = numeric_dates[mask_num].astype(float).astype('Int64').astype(str)
                
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).set_index('date').sort_index()
            
            market_data[s_code] = df
            
        except OSError as e:
            print(f"Skipping {s_code} due to OSError: {e}")
            continue
        except Exception as e:
            print(f"Failed to load {s_code}: {e}")
            continue
            
    print("Computing downstream returns...")
    
    results = []  # Restore this
    
    print(f"Loaded {len(market_data)} symbols in market_data.")
    if len(market_data) > 0:
        print(f"Sample keys: {list(market_data.keys())[:5]}")
        
    fail_count = 0
    
    for idx, row in heroes.iterrows():
        sym = str(row['symbol']).zfill(6)
        pick_time = row['time']
        
        if sym not in market_data:
            if fail_count < 3:
                print(f"Symbol {sym} not in market_data")
                fail_count += 1
            continue
            
        df = market_data[sym]
        
        if pick_time not in df.index:
            if fail_count < 3:
                print(f"Time Mismatch! Pick: {pick_time} ({type(pick_time)})")
                try:
                    # Find closest match
                    closest = df.index[df.index.searchsorted(pick_time)]
                    print(f"Closest index: {closest}")
                except:
                    print(f"Index head: {df.index[:3]}")
                fail_count += 1
            continue
            
        price_0 = df.loc[pick_time]['close']
        
        # Look ahead
        times = [1, 5, 10, 30]
        future_rets = {}
        
        idx_loc = df.index.get_loc(pick_time)
        
        for t in times:
            future_idx = idx_loc + t
            if future_idx < len(df):
                price_t = df.iloc[future_idx]['close']
                ret = (price_t - price_0) / price_0 * 100
                future_rets[f'ret_{t}m'] = ret
            else:
                future_rets[f'ret_{t}m'] = np.nan
                
        # EOD Return
        last_price = df.iloc[-1]['close']
        future_rets['ret_eod'] = (last_price - price_0) / price_0 * 100
        
        res_row = row.to_dict()
        res_row.update(future_rets)
        results.append(res_row)
        
    final_df = pd.DataFrame(results)
    
    # 4. Summary Stats
    print("\n[Analysis Summary]")
    print(f"Total Results: {len(results)}")
    
    final_df = pd.DataFrame(results)
    if final_df.empty:
        print("Final DataFrame is empty.")
        return

    print("\nAverage Returns:")
    print(final_df[['ret_1m', 'ret_5m', 'ret_10m', 'ret_30m', 'ret_eod']].mean())
    
    print("\nWin Rate (>0.5%):")
    print((final_df[['ret_1m', 'ret_5m', 'ret_10m']] > 0.5).mean())
    
    print("\nTrap Rate (<-1.0% in 5m):")
    trap_rate = (final_df['ret_5m'] < -1.0).mean()
    print(f"{trap_rate*100:.2f}%")
    
    final_df.to_csv('hero_performance_analysis.csv', index=False)
    print("\nSaved detail report to hero_performance_analysis.csv")

if __name__ == "__main__":
    analyze_results()
