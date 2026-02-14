# garam_core/strategy/oss_brain_strategy.py
import torch
import pandas as pd
import numpy as np
from .base import BaseStrategy
from scripts.neural_brain import GaramNeuralBrain

class OSSBrainStrategy(BaseStrategy):
    """
    [INTELLIGENCE CORE] OSS 8192-Node Brain Strategy
    - Uses trained neural network to generate long/short signals.
    - Matches features from train_oss_brain.py (SMA-based).
    """
    NAME = "OSSBrain_8192"

    def __init__(self, model_path="core/active_config/neuro_brain_state.pth", threshold=0.015, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize and load model
        print(f"🔄 [{self.NAME}] Loading Brain: {model_path}")
        self.brain = GaramNeuralBrain(input_size=64, mode="MAX")
        state = torch.load(model_path, map_location=self.device, weights_only=True)
        self.brain.load_state_dict(state)
        self.brain.eval()
        self.brain.to(self.device)

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """SMA-based feature extraction matching training logic"""
        closes = df['close']
        volumes = df['volume']
        
        # 1. RSI (SMA 14)
        delta = closes.diff()
        up = delta.clip(lower=0).rolling(window=14).mean()
        down = (-delta.clip(upper=0)).rolling(window=14).mean()
        rs = up / (down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        
        # 2. Volume Ratio (SMA 20)
        vol_ma = volumes.rolling(window=20).mean()
        vol_ratio = volumes / (vol_ma + 1e-9)
        
        # 3. MA Distance (SMA 20)
        ma20 = closes.rolling(window=20).mean()
        ma_dist = (closes / (ma20 + 1e-9)) - 1.0
        
        # 4. Whale & Squeeze
        whale = (vol_ratio > 3.0).astype(float)
        squeeze = ((rsi < 30) & (vol_ratio > 2.0)).astype(float)
        
        # Scaling (Matches train_oss_brain.py)
        f1 = (rsi / 100.0).values
        f2 = (vol_ratio / 10.0).values
        f3 = (ma_dist / 0.1).values
        f4 = whale.values
        f5 = squeeze.values
        
        print(f"   [DEBUG] Feature Stats (Mean): RSI={np.nanmean(f1):.4f}, Vol={np.nanmean(f2):.4f}, MA={np.nanmean(f3):.4f}")
        
        X = np.stack([f1, f2, f3, f4, f5], axis=1)
        return X

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate Buy(1) signals based on brain predictions"""
        X = self.prepare_features(df)
        
        # Filter NaNs for inference
        valid_mask = ~np.isnan(X).any(axis=1)
        X_valid = X[valid_mask]
        
        if len(X_valid) == 0:
            return pd.Series(0, index=df.index)
            
        # Inference
        X_tensor = torch.FloatTensor(X_valid).to(self.device)
        # Pad to 64
        pad = torch.zeros(X_tensor.shape[0], 64 - X_tensor.shape[1], device=self.device)
        X_padded = torch.cat([X_tensor, pad], dim=1)
        
        with torch.no_grad():
            output = self.brain(X_padded)
            # Predicted Return = tanh(output) * 0.15
            pred_ret_tensor = torch.tanh(output[:, 0]) * 0.15
            pred_ret = pred_ret_tensor.cpu().numpy()
            
        print(f"   [DEBUG] Predictions: Mean={pred_ret.mean():.6f}, Std={pred_ret.std():.6f}, Max={pred_ret.max():.6f}, Min={pred_ret.min():.6f}")
            
        # Map back to original index
        signals = np.zeros(len(df))
        # Strategy: Go Long if predicted return > threshold
        sig_val = (pred_ret > self.threshold).astype(float)
        signals[valid_mask] = sig_val
        
        print(f"   [DEBUG] Signals generated: {sig_val.sum()} / {len(sig_val)}")
        
        return pd.Series(signals, index=df.index)
