# garam_core/research/pulse/load_data.py
import pandas as pd
from pathlib import Path
import sys

def load_minute_data(symbol: str, folder: str) -> pd.DataFrame:
    """
    Loads 1-minute data for a symbol from a specified folder.
    Expects CSV format with 'datetime' or 'date' index/column.
    """
    p = Path(folder) / f"{symbol}.csv" # Assuming standardized naming
    if not p.exists():
         # Try with _1m suffix or different convention if standard fails
        p_alt = Path(folder) / f"{symbol}_1m.csv"
        if p_alt.exists():
            p = p_alt
        else:
            raise FileNotFoundError(f"Data for {symbol} not found in {folder}")

    try:
        df = pd.read_csv(p, parse_dates=True)
        # normalize index
        if "datetime" in df.columns:
            df = df.set_index("datetime")
        elif "date" in df.columns:
            df = df.set_index("date")
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        df = df.sort_index()
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load {p}: {e}")

def enhance_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds basic features for Pulse research:
    - return1: 1-minute return
    - vol20: 20-minute rolling std of close
    - vol5: 5-minute rolling std of close
    - avg_volume20: 20-minute rolling mean of volume
    - volume_pressure: volume / avg_volume20
    """
    df = df.copy()
    df["return1"] = df["close"].pct_change().fillna(0)
    df["vol20"] = df["close"].rolling(20).std().fillna(0)
    df["vol5"] = df["close"].rolling(5).std().fillna(0)
    df["avg_volume20"] = df["volume"].rolling(20).mean().fillna(0)
    
    # Avoid div by zero
    df["vol_pressure"] = df["volume"] / df["avg_volume20"].replace(0, 1)
    
    return df
