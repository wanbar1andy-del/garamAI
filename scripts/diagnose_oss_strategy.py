"""
OSSBrainStrategy Diagnostic Script
"""
import sys
import pandas as pd
import numpy as np
import torch
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from garam_core.strategy.oss_brain_strategy import OSSBrainStrategy

def diagnose():
    cache_path = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"
    print(f"🔄 Loading data: {cache_path}")
    cached = pd.read_pickle(cache_path)
    closes = cached['closes']
    volumes = cached['volumes']
    
    symbol = "005930"
    df = pd.DataFrame({
        'close': closes[symbol],
        'volume': volumes[symbol]
    }).dropna().tail(1000)
    
    print(f"📊 Testing on {len(df)} bars for {symbol}")
    
    strategy = OSSBrainStrategy(threshold=0.001)
    
    # Raw value test
    X = strategy.prepare_features(df)
    valid_mask = ~np.isnan(X).any(axis=1)
    X_valid = X[valid_mask]
    
    X_tensor = torch.FloatTensor(X_valid).to(strategy.device)
    pad = torch.zeros(X_tensor.shape[0], 64 - X_tensor.shape[1], device=strategy.device)
    X_padded = torch.cat([X_tensor, pad], dim=1)
    
    with torch.no_grad():
        raw_out = strategy.brain(X_padded)[:, 0]
        pred_ret = torch.tanh(raw_out) * 0.15
        
    print(f"   [RAW] Raw Out (Pre-tanh): Mean={raw_out.mean():.4f}, Std={raw_out.std():.4f}, Max={raw_out.max():.4f}")
    print(f"   [PRED] Predicted: Mean={pred_ret.mean():.6f}")
    
    # Layer Bias Inspection
    print("\n🔍 Layer Bias Inspection:")
    with torch.no_grad():
        entry_bias = strategy.brain.entry[0].bias
        head_bias = strategy.brain.head.bias
        print(f"   - Entry[0] Bias: Mean={entry_bias.mean():.4f}, Std={entry_bias.std():.4f}, Max={entry_bias.max():.4f}, Min={entry_bias.min():.4f}")
        print(f"   - Head Bias:     {head_bias.cpu().numpy().flatten()}")
    
    # Zero input test
    zero_in = torch.zeros(1, 64).to(strategy.device)
    with torch.no_grad():
        zero_out = strategy.brain(zero_in)[:, 0]
    print(f"   [ZERO] Zero-Input Output: {zero_out.item():.6f}")
    
    print(f"\n✅ Diagnostic Finished")

if __name__ == "__main__":
    diagnose()
