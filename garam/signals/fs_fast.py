"""
fs_fast: Ultra-short term direction score
"""

import numpy as np
import pandas as pd
from .utils import FsFastParams

def compute_fs_fast(
    df: pd.DataFrame,
    params: FsFastParams
) -> pd.Series:
    """
    Compute fs_fast score for a given DataFrame.
    
    Args:
        df: DataFrame with 'close' and 'volume' columns (index: datetime)
        params: FsFastParams object
        
    Returns:
        pd.Series: fs_fast score (index: datetime)
    """
    # Ensure float types
    close = df["close"].astype(float)
    volume = df["volume"].astype(float)
    
    k = params.k_return
    N_ret = params.N_ret
    M_vol = params.M_vol
    M_dir = params.M_dir
    N_fs = params.N_fs
    eps = params.eps
    
    # 1. Price Momentum Z-Score
    # Log returns
    ret = np.log(close / close.shift(1))
    # k-bar cumulative log return
    r_k = np.log(close / close.shift(k))
    # Rolling volatility of returns
    sigma_ret = ret.rolling(N_ret).std()
    # Adjusted momentum z-score (t-stat like)
    z_price = r_k / (sigma_ret * np.sqrt(k) + eps)
    
    # 2. Volume Surprise Z-Score
    vol_ma = volume.rolling(M_vol).mean()
    vol_std = volume.rolling(M_vol).std()
    z_vol = (volume - vol_ma) / (vol_std + eps)
    
    # 3. Directional Consistency (up_ratio)
    is_up = (ret > 0).astype(float)
    up_ratio = is_up.rolling(M_dir).mean()
    s_dir = 2.0 * up_ratio - 1.0  # Scale to [-1, 1]
    
    # 4. Raw Score Combination
    s_raw = (
        params.w_price * z_price +
        params.w_vol * z_vol +
        params.w_dir * s_dir
    )
    
    # 5. Normalization (Z-score of raw score)
    sigma_fs = s_raw.rolling(N_fs).std()
    fs = s_raw / (sigma_fs + eps)
    
    # 6. Clipping
    fs_clipped = fs.clip(lower=-params.clip_L, upper=params.clip_L)
    
    fs_clipped.name = "fs_fast"
    return fs_clipped

def update_fs_fast_one_tick(
    history: pd.DataFrame,
    params: FsFastParams
) -> float:
    """
    Compute fs_fast for the last bar in history.
    Useful for real-time updates.
    """
    fs_series = compute_fs_fast(history, params)
    return float(fs_series.iloc[-1])
