"""
Test fs_fast signal logic
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from garam.signals.utils import FsFastParams
from garam.signals.fs_fast import compute_fs_fast

def generate_synthetic_data(length=500, mode='trend'):
    """Generate synthetic OHLCV data"""
    np.random.seed(42)
    
    # Base price path
    returns = np.random.normal(0, 0.001, length)
    
    if mode == 'trend':
        # Add trend component
        trend = np.linspace(0, 0.05, length) # 5% up trend
        returns += np.diff(trend, prepend=0)
    elif mode == 'range':
        # Mean reverting
        pass
    elif mode == 'crash':
        # Sudden drop
        returns[300:320] -= 0.01 # -1% per bar for 20 bars
        
    price = 100 * np.exp(np.cumsum(returns))
    
    # Volume (random with spikes)
    volume = np.random.lognormal(10, 1, length)
    if mode == 'trend':
        # Volume spike during trend
        volume[100:150] *= 2.0
        
    df = pd.DataFrame({
        'close': price,
        'volume': volume
    }, index=pd.date_range('2025-01-01', periods=length, freq='1min'))
    
    return df

def test_fs_fast():
    print("Testing fs_fast signal...")
    
    # 1. Trend Scenario
    print("\nScenario 1: Uptrend with Volume Spike")
    df_trend = generate_synthetic_data(mode='trend')
    params = FsFastParams()
    fs_trend = compute_fs_fast(df_trend, params)
    
    print(f"Mean fs_fast: {fs_trend.mean():.4f}")
    print(f"Max fs_fast: {fs_trend.max():.4f}")
    print(f"Min fs_fast: {fs_trend.min():.4f}")
    
    # Check if it captures the trend (positive score)
    high_score_ratio = (fs_trend > 1.0).mean()
    print(f"Ratio > 1.0: {high_score_ratio:.2%}")
    
    # 2. Range Scenario
    print("\nScenario 2: Ranging Market")
    df_range = generate_synthetic_data(mode='range')
    fs_range = compute_fs_fast(df_range, params)
    
    print(f"Mean fs_fast: {fs_range.mean():.4f}")
    print(f"Max fs_fast: {fs_range.max():.4f}")
    print(f"Min fs_fast: {fs_range.min():.4f}")
    
    # Should be mostly near 0
    near_zero_ratio = ((fs_range > -1.0) & (fs_range < 1.0)).mean()
    print(f"Ratio in [-1, 1]: {near_zero_ratio:.2%}")
    
    # 3. Crash Scenario
    print("\nScenario 3: Crash")
    df_crash = generate_synthetic_data(mode='crash')
    fs_crash = compute_fs_fast(df_crash, params)
    
    print(f"Mean fs_fast: {fs_crash.mean():.4f}")
    print(f"Min fs_fast: {fs_crash.min():.4f}")
    
    # Check crash detection
    crash_detection = (fs_crash < -2.0).any()
    print(f"Crash Detected (fs < -2.0): {crash_detection}")

if __name__ == "__main__":
    test_fs_fast()
