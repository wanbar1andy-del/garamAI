import pandas as pd
import numpy as np

def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Average True Range.
    Requires: high, low, close
    """
    df = df.copy()
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift(1))
    df['tr2'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    
    # Wilder's Smoothing
    alpha = 1/period
    df['atr'] = df['tr'].ewm(alpha=alpha, adjust=False).mean()
    
    df.drop(columns=['tr0', 'tr1', 'tr2', 'tr'], inplace=True, errors='ignore')
    return df

def calc_realized_vol(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Calculate Realized Volatility (std dev of log returns).
    Annualized assuming 252 trading days.
    """
    df = df.copy()
    df['log_ret'] = np.log(df['close'] / df['close'].shift(1))
    df['realized_vol'] = df['log_ret'].rolling(window=window).std() * np.sqrt(252)
    df.drop(columns=['log_ret'], inplace=True, errors='ignore')
    return df

def calc_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.
    Adds: 'bb_upper', 'bb_lower', 'bb_width', 'bb_pct_b'
    """
    df = df.copy()
    sma = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    
    df['bb_upper'] = sma + (std * num_std)
    df['bb_lower'] = sma - (std * num_std)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma
    df['bb_pct_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    return df
