# garam_core/fastlane/feature_store.py
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List

from ..health.gate import gate_environment
from ..data.loader import load_ohlcv, LoadSpec

class FeatureStore:
    def __init__(self, cache_dir: str = "cache/features"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Data path resolution delegated to Gate/Loader at runtime

    def get_features(self, symbol: str, force_recompute: bool = False) -> pd.DataFrame:
        """
        Returns DataFrame with: date, close, vol_20, mom_20, zscore, rsi_14, bb_mid_20, bb_up_20, bb_low_20, ma_60
        """
        cache_path = self.cache_dir / f"{symbol}_features.parquet"
        
        if not force_recompute and cache_path.exists():
            try:
                return pd.read_parquet(cache_path)
            except Exception as e:
                print(f"[FeatureStore] Cache corrupted for {symbol}, recomputing... ({e})")

        return self._compute_and_cache(symbol, cache_path)

    def _compute_and_cache(self, symbol: str, cache_path: Path) -> pd.DataFrame:
        try:
            # Resolve Paths via Core Gate
            project_root = Path(__file__).resolve().parent.parent
            paths = gate_environment(project_root)
            
            # Load Data via Core Loader (SSOT)
            df = load_ohlcv(
                data_root=paths.data_root, 
                symbol=symbol, 
                timeframe="minute",
                spec=LoadSpec(tz="Asia/Seoul")
            )
            
        except Exception as e:
            raise FileNotFoundError(f"FeatureStore failed to load data for {symbol}: {e}")

        # Compute Features
        close = df["close"]
        
        # 1. Volatility (20) & Momentum (20)
        rets = close.pct_change()
        vol_20 = rets.rolling(window=20).std().fillna(0.0)
        mom_20 = close.pct_change(periods=20).fillna(0.0)
        
        # 2. Z-Score (Mom/Vol)
        zscore = np.divide(mom_20, vol_20, out=np.zeros_like(mom_20), where=vol_20 > 1e-9)
        
        # 3. RSI (14) - Wilder's Smoothing
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).fillna(0.0)
        loss = (-delta.where(delta < 0, 0)).fillna(0.0)
        
        # com=13 is equivalent to alpha=1/14 for Wilder's 
        avg_gain = gain.ewm(com=13, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(com=13, min_periods=14, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi_14 = 100.0 - (100.0 / (1.0 + rs))
        rsi_14 = rsi_14.fillna(50.0) # Default mid
        
        # 4. Bollinger Bands (20, 2)
        bb_mid_20 = close.rolling(window=20).mean()
        bb_std_20 = close.rolling(window=20).std()
        bb_up_20 = bb_mid_20 + (2.0 * bb_std_20)
        bb_low_20 = bb_mid_20 - (2.0 * bb_std_20)
        
        # 5. Trend Filter (MA 60)
        ma_60 = close.rolling(window=60).mean().fillna(close) 
        
        # Assemble
        df_feats = pd.DataFrame({
            "date": df.index,
            "close": close.values,
            "vol_20": vol_20.values,
            "mom_20": mom_20.values,
            "zscore": zscore.values,
            
            # Phase 20 Features
            "rsi_14": rsi_14.values,
            "bb_mid_20": bb_mid_20.values,
            "bb_up_20": bb_up_20.values,
            "bb_low_20": bb_low_20.values,
            "ma_60": ma_60.values
        })
        
        df_feats.to_parquet(cache_path, compression="snappy")
        return df_feats
