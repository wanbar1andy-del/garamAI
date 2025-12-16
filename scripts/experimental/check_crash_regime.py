import sys
import os
import pandas as pd
from pathlib import Path

# Setup Path
sys.path.append(os.path.abspath("C:/garam/garam"))
try:
    from config import PATHS
except ImportError:
    from garam.config import PATHS
from garam.engine.components.hmm_detector import HMMRegimeDetector

def check_crash_regime():
    # Load KOSPI
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    df_mkt = pd.read_csv(kospi_path)
    col_map = {c: c.lower() for c in df_mkt.columns}
    df_mkt.rename(columns=col_map, inplace=True)
    date_col = 'timestamp' if 'timestamp' in df_mkt.columns else 'date'
    df_mkt[date_col] = pd.to_datetime(df_mkt[date_col])
    df_mkt.set_index(date_col, inplace=True)
    df_mkt.sort_index(inplace=True)
    
    # Train HMM on data BEFORE 2024 (approx)
    hmm = HMMRegimeDetector()
    train_end = pd.Timestamp("2024-01-01")
    hmm.train(df_mkt[df_mkt.index < train_end]['close'])
    
    # Predict around March 24, 2025
    target_date = pd.Timestamp("2025-03-24")
    start_look = target_date - pd.Timedelta(days=20)
    end_look = target_date + pd.Timedelta(days=5)
    
    subset = df_mkt[(df_mkt.index >= start_look) & (df_mkt.index <= end_look)]
    
    print(f"=== Regime Analysis around Crash ({target_date.date()}) ===")
    for date, row in subset.iterrows():
        # Predict using data up to this date
        recent = df_mkt.loc[:date]['close'].tail(50)
        regime = hmm.predict_regime(recent)
        close = row['close']
        ret = row['close'] / df_mkt.loc[:date]['close'].iloc[-2] - 1.0 if len(df_mkt.loc[:date]) > 1 else 0
        
        marker = " <--- CRASH" if date.date() == target_date.date() else ""
        print(f"{date.date()}: Close={close:.0f}, Ret={ret*100:.2f}%, Regime={regime}{marker}")

if __name__ == "__main__":
    check_crash_regime()
