"""
Build Intraday Features for A2 Alpha
- Processes minute data to extract intraday trend metrics.
- Output: Intraday features file (Parquet/CSV)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os
from datetime import time

def process_symbol(symbol, file_path):
    try:
        df = pd.read_csv(file_path)
        if df.empty: return None
        
        # Normalize columns
        df.columns = [c.lower() for c in df.columns]
        
        # Parse datetime
        if 'date' in df.columns:
            # Check if date column has time component (length > 10 usually)
            # Or just try to_datetime
            try:
                df['datetime'] = pd.to_datetime(df['date'])
            except:
                if 'time' in df.columns:
                     df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str).str.zfill(4), format='%Y%m%d %H%M')
                else:
                    return None
        elif 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'])
        else:
            return None
            
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)
        
        # Morning: 09:00 ~ 10:30
        # Afternoon (Pre-close): 10:30 ~ 15:20
        # Close: 15:30 (or last tick)
        
        # We need daily aggregation.
        # Group by Date
        daily_groups = df.groupby(df.index.date)
        
        results = []
        
        for date, day_df in daily_groups:
            if day_df.empty: continue
            
            # 1. Prices
            # Open (09:00)
            p_open = day_df.iloc[0]['open']
            
            # Morning Close (10:30)
            # Find tick closest to 10:30 <= 10:30
            morning_df = day_df.between_time('09:00', '10:30')
            if morning_df.empty: continue
            p_morning = morning_df.iloc[-1]['close']
            v_morning = morning_df['volume'].sum()
            
            # Pre-close (15:20)
            # Find tick closest to 15:20 <= 15:20
            # If data ends before 15:20, take last
            preclose_df = day_df.between_time('10:30', '15:20')
            if preclose_df.empty:
                # Fallback: if no afternoon data, skip or use close
                p_preclose = day_df.iloc[-1]['close']
            else:
                p_preclose = preclose_df.iloc[-1]['close']
                
            # Day Stats
            p_close = day_df.iloc[-1]['close']
            p_high = day_df['high'].max()
            p_low = day_df['low'].min()
            v_day = day_df['volume'].sum()
            
            # 2. Features
            # Morning Return
            if p_open > 0:
                ret_m = (p_morning - p_open) / p_open
            else:
                ret_m = 0.0
                
            # Afternoon Return
            if p_morning > 0:
                ret_a = (p_preclose - p_morning) / p_morning
            else:
                ret_a = 0.0
                
            # Trend Quality q_t
            # User Spec: "Consistent Trend".
            # Original Formula: sign(r_m) * min(|r_m|, |r_a|) -> Flawed if signs differ.
            # Fix: Only valid if signs match.
            if np.sign(ret_m) == np.sign(ret_a):
                q_t = np.sign(ret_m) * min(abs(ret_m), abs(ret_a))
            else:
                # Penalize volatility/reversal? Or just 0?
                # User said "0 or near 0". Let's make it 0 to be safe.
                # Actually, if it reverses, it's bad trend. Maybe negative?
                # But A2 is "Trend Alpha". 0 means "No Trend".
                q_t = 0.0
            
            # Range Position
            # (C - L) / (H - L + eps)
            denom = p_high - p_low
            if denom == 0: denom = 1.0 # Avoid div/0
            range_pos = (p_close - p_low) / denom
            
            results.append({
                'date': date,
                'symbol': symbol,
                'intraday_morning_ret': ret_m,
                'intraday_afternoon_ret': ret_a,
                'intraday_trend_q': q_t,
                'intraday_range_pos': range_pos,
                'daily_volume': v_day
            })
            
        return pd.DataFrame(results)
        
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        return None

def main():
    print("Building Intraday Features...")
    
    minute_dir = Path("g:/내 드라이브/garamdata/history/minute")
    output_dir = Path("c:/garam/garam/GARAM_Data")
    output_dir.mkdir(exist_ok=True)
    
    all_features = []
    
    files = list(minute_dir.glob("*_1m.csv"))
    print(f"Found {len(files)} minute files.")
    
    for i, f in enumerate(files):
        symbol = f.stem.split('_')[0]
        # print(f"Processing {symbol} ({i+1}/{len(files)})...")
        
        df_feat = process_symbol(symbol, f)
        if df_feat is not None and not df_feat.empty:
            all_features.append(df_feat)
            
    if not all_features:
        print("No features generated.")
        return
        
    # Combine
    full_df = pd.concat(all_features, ignore_index=True)
    full_df['date'] = pd.to_datetime(full_df['date'])
    
    # Calculate Volume Pressure (vol_rel)
    # Requires 20d MA of volume per symbol
    print("Calculating Volume Pressure...")
    
    # Pivot volume to wide format for rolling calc
    vol_wide = full_df.pivot(index='date', columns='symbol', values='daily_volume')
    vol_ma20 = vol_wide.rolling(window=20).mean()
    
    # Stack back to long format
    vol_ma20_long = vol_ma20.stack().rename('vol_ma20').reset_index()
    
    # Merge
    full_df = pd.merge(full_df, vol_ma20_long, on=['date', 'symbol'], how='left')
    
    # Calc vol_rel = log(1 + V_d / V_ma20)
    full_df['vol_ma20'] = full_df['vol_ma20'].replace(0, np.nan)
    full_df['intraday_vol_rel'] = np.log1p(full_df['daily_volume'] / full_df['vol_ma20'])
    full_df['intraday_vol_rel'] = full_df['intraday_vol_rel'].fillna(0.0)
    
    # Save
    # Pivot to Wide Format for each feature (easier for Alpha Engine)
    # We need dict of DataFrames: {feature: df_wide}
    # But saving as one big Parquet is better for storage.
    # Let's save as MultiIndex Parquet.
    
    full_df.set_index(['date', 'symbol'], inplace=True)
    
    output_file = output_dir / "intraday_features.parquet"
    try:
        full_df.to_parquet(output_file)
        print(f"Saved to {output_file}")
    except Exception as e:
        print(f"Parquet save failed: {e}. Falling back to CSV.")
        full_df.to_csv(output_dir / "intraday_features.csv")
        print(f"Saved to {output_dir / 'intraday_features.csv'}")

if __name__ == "__main__":
    main()
