"""
Calculate Suitability Scores for DGE Final Strategy
Inputs: Universe CSV, Date Range
Outputs: Daily Score CSV (symbol, date, score)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime, timedelta
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from regime.edge_meter import EdgeMeter, MarketState

def calculate_suitability(daily_df):
    """
    Calculate daily suitability score (0.0 ~ 1.0)
    Logic (Champion Rule v2):
    1. Regime Classification (EdgeMeter)
    2. Edge Lookup (Simplified for now: R1/R2=High, R3=Low, R4-R7=Zero)
    3. Score Assignment:
       - R1 (Strong Up): 0.8 ~ 1.0
       - R2 (Grind Up): 0.5 ~ 0.7
       - R3 (Chop): 0.0 ~ 0.14 (Strictly < Gate 0.15)
       - R4~R7 (Down/Event): 0.0
    """
    df = daily_df.copy()
    
    # Initialize EdgeMeter
    meter = EdgeMeter()
    
    scores = []
    
    # Iterate through days to calculate regime (simulating live)
    # Note: EdgeMeter needs history. We can optimize by vectorizing or rolling.
    # For now, let's use a simplified vectorized approach matching EdgeMeter logic.
    
    # 1. Trend (MA20)
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # 2. Volatility (ATR)
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                     abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(14).mean()
    df['atr_pct'] = df['atr'] / df['close']
    
    # 3. Regime Classification & Scoring
    # R1: Close > MA20 & MA20 > MA60 & Close > Close(20d)*1.05 (Strong Momentum)
    # R2: Close > MA20 (Grind)
    # R3: Close < MA20 but > MA60 (Chop/Pullback)
    # R4: Close < MA60 (Down)
    
    # Vectorized Logic
    cond_ma20_up = (df['close'] > df['ma20'])
    cond_ma60_up = (df['close'] > df['ma60'])
    cond_strong = (df['close'] > df['close'].shift(20) * 1.05)
    
    # Default 0.0
    df['final_score'] = 0.0
    
    # R1 (Strong Up) -> Score 0.8 ~ 1.0
    # Boost if Volatility is healthy (1~4%)
    r1_mask = cond_ma20_up & cond_strong
    df.loc[r1_mask, 'final_score'] = 0.8
    df.loc[r1_mask & (df['atr_pct'] >= 0.01) & (df['atr_pct'] <= 0.04), 'final_score'] = 1.0
    
    # R2 (Grind Up) -> Score 0.5 ~ 0.7
    r2_mask = cond_ma20_up & ~cond_strong
    df.loc[r2_mask, 'final_score'] = 0.5
    df.loc[r2_mask & (df['atr_pct'] >= 0.01) & (df['atr_pct'] <= 0.04), 'final_score'] = 0.7
    
    # R3 (Chop) -> Score 0.0 ~ 0.14 (Strictly < 0.15)
    # We allow a small score to observe, but Gate will block it.
    r3_mask = ~cond_ma20_up & cond_ma60_up
    df.loc[r3_mask, 'final_score'] = 0.14 # Capped
    
    # R4~R7 (Down) -> Score 0.0
    # Already 0.0 by default
    
    return df[['final_score']]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--universe-file', required=True)
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    parser.add_argument('--output-file', required=True)
    args = parser.parse_args()
    
    universe = pd.read_csv(args.universe_file)
    symbols = universe['symbol'].astype(str).str.zfill(6).tolist()
    
    all_scores = []
    
    print(f"Calculating scores for {len(symbols)} symbols...")
    
    # Mock Data Generation for Demo (Since we don't have 100 files yet)
    # In production, this would load actual CSVs
    dates = pd.date_range(args.start_date, args.end_date, freq='B')
    
    # Real Data Fetching Logic
    # We need to fetch daily data for each symbol
    # Since we are in a 64-bit environment (likely), we can't call Kiwoom directly here if it requires 32-bit.
    # However, we have 'fetch_history_kiwoom.py' which is a 32-bit script.
    # Strategy:
    # 1. Check if data exists in 'garamdata/history/daily/{symbol}.csv'
    # 2. If not, trigger 'fetch_history_kiwoom.py' (or similar) to download it.
    # For this verification, we will assume the user wants us to DOWNLOAD it now.
    
    # But wait, we are inside a script that might be run by the user.
    # Let's try to load from CSV if exists, else skip (or warn).
    # To properly support "Download on Demand", we need to call the 32-bit fetcher.
    
    import subprocess
    
    # Data Directories
    daily_dir = Path("g:/내 드라이브/garamdata/history/daily")
    minute_dir = Path("g:/내 드라이브/garamdata/history/minute")
    
    for symbol in symbols:
        daily_file = daily_dir / f"{symbol}_daily.csv"
        minute_file = minute_dir / f"{symbol}_1m.csv"
        
        df = None
        
        # 1. Try Daily File
        if daily_file.exists():
            try:
                df = pd.read_csv(daily_file)
                # Standardize columns
                df.rename(columns={'일자': 'date', '현재가': 'close', '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'}, inplace=True)
                if 'date' not in df.columns and 'timestamp' in df.columns:
                    df.rename(columns={'timestamp': 'date'}, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
            except Exception as e:
                print(f"Error reading daily file for {symbol}: {e}")
                
        # 2. If no daily, Try Minute File & Resample
        if df is None and minute_file.exists():
            try:
                # print(f"Resampling minute data for {symbol}...")
                m_df = pd.read_csv(minute_file)
                m_df['date'] = pd.to_datetime(m_df['date'])
                m_df.set_index('date', inplace=True)
                m_df.sort_index(inplace=True)
                
                # Resample to Daily
                df = m_df.resample('D').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                # Filter out days with no volume/data if any
                df = df[df['volume'] > 0]
                
            except Exception as e:
                print(f"Error resampling minute file for {symbol}: {e}")

        if df is None or df.empty:
            print(f"No data found for {symbol} (Checked Daily & Minute).")
            continue

        try:
            # Filter Date Range
            mask = (df.index >= args.start_date) & (df.index <= args.end_date)
            df_slice = df.loc[mask]
            
            if df_slice.empty:
                print(f"No data for {symbol} in range {args.start_date} ~ {args.end_date}.")
                continue
                
            scores = calculate_suitability(df_slice)
            scores['symbol'] = symbol
            all_scores.append(scores)
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    if not all_scores:
        print("No scores calculated. Please ensure data is downloaded.")
        return

    final_df = pd.concat(all_scores).reset_index()
    final_df.rename(columns={'date': 'date', 'final_score': 'score'}, inplace=True)
    
    # Save
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(args.output_file, index=False)
    print(f"Saved scores to {args.output_file}")

if __name__ == "__main__":
    main()
