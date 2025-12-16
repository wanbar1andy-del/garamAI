import pandas as pd
import numpy as np

def calc_ma_trend(df: pd.DataFrame, fast: int = 20, slow: int = 60) -> pd.DataFrame:
    """
    Calculate Moving Average based trend.
    Adds: 'ma_fast', 'ma_slow', 'trend_score' (1.0 for Bull, -1.0 for Bear, 0.0 for Neutral)
    """
    df = df.copy()
    df[f'ma_{fast}'] = df['close'].rolling(window=fast).mean()
    df[f'ma_{slow}'] = df['close'].rolling(window=slow).mean()
    
    # Simple Trend Score: 1 if Fast > Slow, -1 if Fast < Slow
    # We can make it more granular later
    df['trend_score'] = np.where(df[f'ma_{fast}'] > df[f'ma_{slow}'], 1.0, -1.0)
    
    # Neutral zone logic (optional): if difference is very small
    # threshold = df['close'] * 0.005
    # df.loc[abs(df[f'ma_{fast}'] - df[f'ma_{slow}']) < threshold, 'trend_score'] = 0.0
    
    return df

def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Calculate MACD."""
    df = df.copy()
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd_line'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd_line'].ewm(span=signal, adjust=False).mean()
    df['macd_hist'] = df['macd_line'] - df['macd_signal']
    return df

def calc_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate ADX (Average Directional Index).
    Requires: high, low, close
    """
    df = df.copy()
    
    # True Range
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift(1))
    df['tr2'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    
    # Directional Movement
    df['up_move'] = df['high'] - df['high'].shift(1)
    df['down_move'] = df['low'].shift(1) - df['low']
    
    df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0.0)
    df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0.0)
    
    # Smooth
    # Wilder's Smoothing (Alpha = 1/n)
    alpha = 1/period
    df['tr_smooth'] = df['tr'].ewm(alpha=alpha, adjust=False).mean()
    df['plus_di'] = 100 * (df['plus_dm'].ewm(alpha=alpha, adjust=False).mean() / df['tr_smooth'])
    df['minus_di'] = 100 * (df['minus_dm'].ewm(alpha=alpha, adjust=False).mean() / df['tr_smooth'])
    
    # DX
    df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
    
    # ADX
    df['adx'] = df['dx'].ewm(alpha=alpha, adjust=False).mean()
    
    # Cleanup temp columns
    cols_to_drop = ['tr0', 'tr1', 'tr2', 'tr', 'up_move', 'down_move', 'plus_dm', 'minus_dm', 'tr_smooth', 'dx']
    df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
    
    return df
