"""
OSS Brain Inference 테스트 스크립트 (V3 - SMA Alignment)

목적: 훈련된 8192-node Brain의 추론 성능 검증 (SMA 14 Tap 반영)
"""

import torch
import pandas as pd
import numpy as np
import time
from pathlib import Path
import sys

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.neural_brain import GaramNeuralBrain

def prepare_features_sma(closes_df, volumes_df, target_returns_df):
    """
    Standalone feature engineering (matches train_oss_brain.py SMA logic)
    """
    # 1. RSI (SMA via rolling)
    delta = closes_df.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    # train_oss_brain uses torch.ones(1,1,span)/span (SMA)
    avg_gain = up.rolling(window=14).mean()
    avg_loss = down.rolling(window=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    
    # 2. Volume Ratio
    vol_ma = volumes_df.rolling(window=20).mean()
    vol_ratio = volumes_df / (vol_ma + 1e-9)
    
    # 3. MA Distance
    ma20 = closes_df.rolling(window=20).mean()
    ma_dist = (closes_df / (ma20 + 1e-9)) - 1.0
    
    # 4. Whale & Squeeze
    whale = (vol_ratio > 3.0).astype(float)
    squeeze = ((rsi < 30) & (vol_ratio > 2.0)).astype(float)
    
    # Flatten and Scale
    f1 = (rsi / 100.0).values.flatten()
    f2 = (vol_ratio / 10.0).values.flatten()
    f3 = (ma_dist / 0.1).values.flatten()
    f4 = whale.values.flatten()
    f5 = squeeze.values.flatten()
    
    X = np.stack([f1, f2, f3, f4, f5], axis=1)
    y = target_returns_df.values.flatten()
    
    # Valid mask (must match trainer's t_closes > 0 & t_volumes > 0)
    valid_mask = (closes_df.values > 0) & (volumes_df.values > 0)
    valid_mask_f = valid_mask.flatten()
    
    # Final NaN check
    X_valid = X[valid_mask_f]
    y_valid = y[valid_mask_f]
    
    nan_mask = ~(np.isnan(X_valid).any(axis=1) | np.isnan(y_valid))
    
    return X_valid[nan_mask], y_valid[nan_mask]

def test_model_loading():
    print("=" * 70)
    print("STEP 1: 모델 로드 검증")
    print("=" * 70)
    
    try:
        brain = GaramNeuralBrain(input_size=64, mode="MAX")
        state_path = "core/active_config/neuro_brain_state.pth"
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        state = torch.load(state_path, map_location=device, weights_only=True)
        brain.load_state_dict(state)
        brain.eval()
        
        params = sum(p.numel() for p in brain.parameters())
        print(f"✅ 로드 성공! (파라미터: {params:,})")
        return brain
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        raise

def test_performance(brain):
    print("\n" + "=" * 70)
    print("STEP 2-4: 성능 및 정확도 분석 (SMA ALIGNED)")
    print("=" * 70)
    
    try:
        cache_path = "cache/market_matrix_8m.pkl"
        print(f"🔄 데이터 로딩: {cache_path}")
        cached = pd.read_pickle(cache_path)
        closes = cached['closes']
        volumes = cached['volumes']
        
        print(f"🔄 SMA 특성 및 타겟 계산 중...")
        # Target calculation on GPU was shift(-120)
        future_returns = (closes.shift(-120) / closes) - 1.0
        future_returns = future_returns.clip(-0.15, 0.15)
        
        X, y = prepare_features_sma(closes, volumes, future_returns)
        
        # Sampling for evaluation (last 200K samples)
        X_val = X[-200000:]
        y_val = y[-200000:]
        
        print(f"🔄 GPU 추론 실행 중 ({len(X_val):,} 샘플)...")
        device = next(brain.parameters()).device
        X_tensor = torch.FloatTensor(X_val).to(device)
        
        y_preds = []
        batch_size = 10000
        
        with torch.no_grad():
            for i in range(0, len(X_tensor), batch_size):
                batch_X = X_tensor[i:i+batch_size]
                pad = torch.zeros(batch_X.shape[0], 64 - batch_X.shape[1], device=device)
                batch_X_padded = torch.cat([batch_X, pad], dim=1)
                
                output = brain(batch_X_padded)
                # predicted_return = torch.tanh(output[:, 0:1]) * 0.15
                pred = torch.tanh(output[:, 0]) * 0.15
                y_preds.append(pred.cpu().numpy())
        
        y_pred = np.concatenate(y_preds)
        
        # Metrics
        mse = np.mean((y_pred - y_val) ** 2)
        
        # Direction Acc
        mask = np.abs(y_val) > 0.001
        acc = (np.sign(y_pred[mask]) == np.sign(y_val[mask])).mean()
        
        baseline_mse = 0.007863
        improvement = (baseline_mse - mse) / baseline_mse * 100
        
        print("\n" + "=" * 70)
        print(f"📊 정밀 검증 결과")
        print("=" * 70)
        print(f"✅ MSE Loss:     {mse:.6f} (Baseline: {baseline_mse:.6f})")
        print(f"✅ 지능 개선율:   {improvement:.1f}%")
        print(f"✅ 방향 정확도:   {acc:.2%}")
        print("=" * 70)
        
        if acc > 0.50:
            print(f"🚀 결과: {acc:.1%} 방향 지능 확인! (Random Baseline 50% 초과)")
            print("         8192-Node 아키텍처가 유의미한 패턴을 습득했습니다.")
        else:
            print(f"⚠️ 결과: 방향 지능({acc:.1%})이 기대치 이하입니다.")
            print("         훈련 에포크를 늘리거나 입력 특성을 보강해야 할 수 있습니다.")

    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        brain = test_model_loading()
        test_performance(brain)
    except KeyboardInterrupt:
        print("\n중단됨")
