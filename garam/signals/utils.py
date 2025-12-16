"""
Signal Utilities and Parameters
"""

from dataclasses import dataclass

@dataclass
class FsFastParams:
    """Parameters for fs_fast (Ultra-short term direction score)"""
    k_return: int = 3          # Momentum lookback (bars)
    N_ret: int = 120           # Return volatility lookback (bars)
    M_vol: int = 20            # Volume z-score lookback (bars)
    M_dir: int = 12            # Directional consistency lookback (bars)
    N_fs: int = 120            # Final score normalization lookback (bars)
    
    # Component weights
    w_price: float = 1.0
    w_vol: float = 0.5
    w_dir: float = 0.7
    
    # Clipping
    clip_L: float = 3.0
    
    # Stability
    eps: float = 1e-8
