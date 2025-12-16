"""
Generate Real Scores for Champion Rule Backtest
Calculates Momentum Score (12M - 1M) for Top 50 symbols using 20-year daily data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from config import PATHS

def load_daily_data(symbol):
    # Try multiple paths including labeled_ prefix
    patterns = [
        PATHS.HISTORY_DIR / f"KR_{symbol}_*_daily_20y.csv",
        PATHS.HISTORY_DIR / f"labeled_KR_{symbol}_*_daily_20y.csv",
        PATHS.HISTORY_DIR / f"{symbol}_daily.csv",
        PATHS.DAILY_DIR / f"{symbol}_daily.csv"
    ]
    
    for p in patterns:
        if "*" in str(p):
            matches = list(Path(p.parent).glob(p.name))
            if matches:
                return pd.read_csv(matches[0])
        elif p.exists():
            return pd.read_csv(p)
            
    return None

def calculate_momentum_score(df):
    # date 인덱스 정리
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    elif '일자' in df.columns:
        df['date'] = pd.to_datetime(df['일자'])
        df.set_index('date', inplace=True)

    df.sort_index(inplace=True)

    close = df['close'] if 'close' in df.columns else df['종가']

    # 6M / 1M 모멘텀 (Fit for 1-Year Data)
    # 6M = 120 days, 1M = 20 days
    # We use 6M because we only have ~242 days of data for most symbols.
    ret_6m = close / close.shift(120) - 1.0
    ret_1m = close / close.shift(20) - 1.0

    score = (ret_6m - ret_1m)
    
    # Debug
    # print(f"  Data Len: {len(df)}, Score Valid: {score.notna().sum()}")
    
    return score

def main():
    print("Generating Real Scores (12M - 1M Momentum)...")
    
    # 1. Identify Universe (Top 50 from Minute Data)
    minute_dir = Path("g:/내 드라이브/garamdata/history/minute")
    files = list(minute_dir.glob("*_1m.csv"))
    symbols = [f.stem.split('_')[0] for f in files]
    
    print(f"Found {len(symbols)} symbols in minute data.")
    
    # Save Universe
    univ_path = PATHS.DATA_DIR / "real_universe.csv"
    pd.DataFrame({'symbol': symbols}).to_csv(univ_path, index=False)
    print(f"Saved universe to {univ_path}")
    
    all_scores = []
    
    for sym in symbols:
        df = load_daily_data(sym)
        
        # If no daily data, fallback to minute data (resampled)
        if df is None:
            minute_file = minute_dir / f"{sym}_1m.csv"
            if minute_file.exists():
                m_df = pd.read_csv(minute_file)
                if not m_df.empty:
                    date_col = 'date' if 'date' in m_df.columns else 'timestamp'
                    if date_col in m_df.columns:
                        m_df[date_col] = pd.to_datetime(m_df[date_col])
                        m_df.set_index(date_col, inplace=True)
                        m_df.sort_index(inplace=True)
                        df = m_df['close'].resample('D').last().dropna().to_frame(name='close')
        
        if df is None or df.empty:
            print(f"Warning: No data for {sym}")
            continue
            
        # Standardize columns
        df.columns = [c.lower() for c in df.columns]
        
        # Calculate Score
        scores = calculate_momentum_score(df)
        
        # Create DataFrame
        score_df = pd.DataFrame({
            'date': scores.index,
            'symbol': sym,
            'score': scores.values
        })
        
        all_scores.append(score_df)
        
    # Combine
    if not all_scores:
        print("No scores generated.")
        return

    full_df = pd.concat(all_scores)
    
    # Ensure date is datetime
    full_df['date'] = pd.to_datetime(full_df['date'])
    
    # Filter for relevant period (2024 ~ )
    full_df = full_df[full_df['date'] >= pd.to_datetime('2024-01-01')]
    
    # Save
    output_path = PATHS.DATA_DIR / "real_scores_2024.csv"
    full_df.to_csv(output_path, index=False)
    print(f"Saved scores to {output_path}")

if __name__ == "__main__":
    main()
