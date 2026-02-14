"""
OSS 신경망 조련 스크립트
사령관이 직접 OSS를 훈련시킨다
"""

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent
CACHE_FILE = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"
BRAIN_FILE = PROJECT_ROOT / "core/active_config/neuro_brain_state.pth"

print("=" * 60)
print("🎯 OSS 조련 시작")
print("=" * 60)

# 1. 데이터 로드 & Device 설정
print("\n[1/4] 시장 데이터 로딩...")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"   - 연산 장치: {device}")

with open(CACHE_FILE, 'rb') as f:
    cached = pd.read_pickle(f)
    closes = cached['closes']
    volumes = cached['volumes']

print(f"   - 심볼 수: {closes.shape[1]}")
print(f"   - 기간: {closes.shape[0]} bars")

# 2. 정답 라벨 생성 (미래 수익률)
print("\n[2/4] 정답 라벨 생성 (Future 120m Returns)...")
future_returns = closes.shift(-120) / closes - 1.0
future_returns = future_returns.fillna(0).clip(-0.15, 0.15)  # -15% ~ +15%

print(f"   - 정답 라벨 생성 완료")
print(f"   - 평균 미래 수익률: {future_returns.mean().mean():.2%}")

# 3. 특성 계산
print("\n[3/4] 특성 계산...")
delta = closes.diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rsi = 100 - (100 / (1 + gain / (loss + 1e-9)))

vol_ma = volumes.rolling(window=20).mean()
vol_ratio = volumes / (vol_ma + 1e-9)

ma20 = closes.rolling(window=20).mean()
ma_dist = (closes / (ma20 + 1e-9)) - 1.0

# Whale: 대량 거래 감지
whale = (vol_ratio > 3.0).astype(float)

# Squeeze: RSI < 30 + Volume Spike
squeeze = ((rsi < 30) & (vol_ratio > 2.0)).astype(float)

print("   - RSI, Volume Ratio, MA Distance, Whale, Squeeze 계산 완료")

# 4. 훈련 데이터 준비 (최적화: 10% 샘플링)
# 4. 훈련 데이터 준비 (GPU 가속 벡터화)
print("\n[4/4] 훈련 데이터 준비 (GPU Tensor Loading)...")

# 데이터를 바로 텐서로 변환 (CPU -> GPU)
# [Time, Symbol] 형태
t_closes = torch.tensor(closes.values, dtype=torch.float32, device=device)
t_volumes = torch.tensor(volumes.values, dtype=torch.float32, device=device)

# 결측치 처리 (0으로)
t_closes = torch.nan_to_num(t_closes, nan=0.0)
t_volumes = torch.nan_to_num(t_volumes, nan=0.0)

# 미래 수익률 계산 (GPU 연산)
target_shift = 120
t_future_closes = torch.roll(t_closes, -target_shift, dims=0)
t_future_returns = (t_future_closes / (t_closes + 1e-9)) - 1.0
t_future_returns = torch.clamp(t_future_returns, -0.15, 0.15)
# 마지막 120개는 무효화 (미래 데이터 없음)
t_future_returns[-target_shift:] = 0.0

# 특성 계산 (GPU 연산)
# 1. RSI
delta = t_closes[1:] - t_closes[:-1]
delta = torch.cat([torch.zeros(1, t_closes.shape[1], device=device), delta], dim=0)

up = torch.where(delta > 0, delta, torch.zeros_like(delta))
down = torch.where(delta < 0, -delta, torch.zeros_like(delta))

# Exponential Moving Average (approximate rolling mean for speed)
def ema(x, span):
    alpha = 2 / (span + 1)
    # Simple implementation for tensor (Recursive is slow, using conv1d is complex)
    # For speed, using simple moving average via cumulative sum on CPU or simplified logic
    # Here using simple moving average via conv1d for speed
    # Reshape for conv1d: [Batch(Symbol), Channel(1), Time]
    x_perm = x.permute(1, 0).unsqueeze(1) # [Sym, 1, Time]
    weights = torch.ones(1, 1, span, device=device) / span
    res = torch.nn.functional.conv1d(x_perm, weights, padding=span-1)
    res = res[:, :, :x.shape[0]].permute(2, 0, 1).squeeze(2) # Back to [Time, Sym]
    return res

avg_gain = ema(up, 14)
avg_loss = ema(down, 14)
rs = avg_gain / (avg_loss + 1e-9)
t_rsi = 100 - (100 / (1 + rs))

# 2. Volume Ratio
vol_ma = ema(t_volumes, 20)
t_vol_ratio = t_volumes / (vol_ma + 1e-9)

# 3. MA Distance
ma20 = ema(t_closes, 20)
t_ma_dist = (t_closes / (ma20 + 1e-9)) - 1.0

# 4. Whale & Squeeze
t_whale = (t_vol_ratio > 3.0).float()
t_squeeze = ((t_rsi < 30) & (t_vol_ratio > 2.0)).float()

print("   - GPU 텐서 연산 완료 (RSI, VolRatio, MADist, Whale, Squeeze)")

# Flatten: [Time * Symbol, Features]
# 유효하지 않은 데이터 (초기 노이즈, 마지막 120개) 제외
valid_mask = (t_closes > 0) & (t_volumes > 0)
# [ROUND 5] 수익 극대화 (PnL Maximization - Total War)
print("\n🔥 [CURRICULUM] Round 5: 실전 통합 훈련 (Maximize Profit)")

# Flatten Tensors First
f_rsi = t_rsi.flatten()
f_vol = t_vol_ratio.flatten()
f_ma = t_ma_dist.flatten()
f_whale = t_whale.flatten()
f_squeeze = t_squeeze.flatten()
f_ret = t_future_returns.flatten()
f_valid = valid_mask.flatten()

# 실전 모의고사 (50% Random Sampling)
# 모든 상황을 겪어봐야 함 (상승, 하락, 횡보)
num_total = f_valid.sum()
indices = torch.nonzero(f_valid, as_tuple=True)[0]
# 50% Random Choice
perm = torch.randperm(len(indices), device=device)
indices = indices[perm[:int(len(indices)*0.5)]]

print(f"   - 실전 데이터(50%): {len(indices):,}개 (전체의 {len(indices)/num_total:.1%})")

# Gather features
f1 = f_rsi[indices] / 100.0
f2 = f_vol[indices] / 10.0
f3 = f_ma[indices] / 0.1
f4 = f_whale[indices]
f5 = f_squeeze[indices]

X = torch.stack([f1, f2, f3, f4, f5], dim=1)
y = f_ret[indices].unsqueeze(1)

batch_size = 1024  # 대규모 데이터라 배치 키움
epochs = 1  # OPTIMIZED: 5 -> 1 for RTX 3060 (18 hours per epoch)

print(f"\n✅ GPU 메모리에 데이터 적재 완료!")
print(f"   - 훈련 샘플: {len(X):,}개")
print(f"   - 특성 차원: {X.shape[1]}")
print(f"   - 텐서 크기: {X.element_size() * X.nelement() / 1e6:.1f} MB (VRAM)")

# 5. Load ACTUAL Neural Brain Architecture
import sys
sys.path.append(str(PROJECT_ROOT / "scripts"))
from scripts.neural_brain import GaramNeuralBrain
 
brain = GaramNeuralBrain(input_size=64, mode="MAX").to(device) # Matches padding, lighter model
optimizer = optim.Adam(brain.parameters(), lr=0.0001) # FIXED: 0.001 -> 0.0001 for 8192 Nodes
criterion = nn.MSELoss()

print(f"\n✅ GaramNeuralBrain 로딩 완료 (8192 nodes, 4 ResBlocks)")
print(f"   Device: {device}")

# 6. 훈련
print("\n" + "=" * 60)
# 6. 훈련 (Direct GPU Tensor Slicing - NO DATALOADER)
print("\n" + "=" * 60)
print("🔥 조련 시작 (DIRECT GPU ACCESS)")
print(f"   - GPU: {torch.cuda.get_device_name(0)}")
print("=" * 60)

# DataLoader 제거 (Windows Deadlock 방지)
# 데이터가 이미 GPU에 있으므로 직접 슬라이싱이 가장 빠름
# batch_size = 256  # 256으로 확실히 줄여서 테스트

# epochs already set to 20 above

# Train/Val Split (90% / 10%)
# Train/Val Split (90% / 10%)
split_idx = int(len(X) * 0.9)
X_train, X_val = X[:split_idx], X[split_idx:]
y_train, y_val = y[:split_idx], y[split_idx:]

print(f"   - Train: {len(X_train):,} / Val: {len(X_val):,}")
print(f"   - 배치 크기: {batch_size}")

# Training Loop with WEIGHTED LOSS
# 수익이 큰 구간(High Return)에 가중치를 더 줌
# 대박을 놓치는 것을 더 큰 실수로 간주함
weight_mask = (torch.abs(y_train) > 0.03).float() * 5.0 + 1.0  # y_train 기준

for epoch in range(epochs):
    brain.train()
    total_loss = 0
    
    # Shuffle Train Data
    perm = torch.randperm(X_train.size(0), device=device)
    X_train = X_train[perm]
    y_train = y_train[perm]
    weight_mask = weight_mask[perm]
    
    # Manual Batching inside Loop
    num_batches = (len(X_train) + batch_size - 1) // batch_size
    
    print(f"\n[Epoch {epoch+1}] 훈련 시작 (Total Batches: {num_batches})")
    
    for i in range(0, len(X_train), batch_size):
        if i % (batch_size * 50) == 0:
            print(f"   -> Batch {i // batch_size}/{num_batches}", end='\r')
            
        batch_X = X_train[i:i+batch_size]
        batch_y = y_train[i:i+batch_size]
        batch_w = weight_mask[i:i+batch_size]
        
        # Padding to 64
        pad_size = 64 - batch_X.shape[1]
        batch_X_padded = torch.cat([batch_X, torch.zeros(batch_X.shape[0], pad_size, device=device)], dim=1)
        
        optimizer.zero_grad()
        output = brain(batch_X_padded)
        predicted_return = torch.tanh(output[:, 0:1]) * 0.15
        
        # Weighted MSE Loss
        loss = (predicted_return - batch_y) ** 2
        loss = (loss * batch_w).mean() # Apply weights
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    avg_train_loss = total_loss / num_batches
    print(f"\n   -> 훈련 완료. 검증 시작...")
    
    # Validation Loop (No Grad)
    brain.eval()
    with torch.no_grad():
        # Batching validation to save memory
        val_loss = 0
        correct_direction = 0
        total_val = 0
        
        for i in range(0, len(X_val), batch_size):
            batch_X = X_val[i:i+batch_size]
            batch_y = y_val[i:i+batch_size]
            
            pad_size = 64 - batch_X.shape[1]
            batch_X_padded = torch.cat([batch_X, torch.zeros(batch_X.shape[0], pad_size, device=device)], dim=1)
            
            output = brain(batch_X_padded)
            predicted = torch.tanh(output[:, 0:1]) * 0.15
            
            loss = criterion(predicted, batch_y)
            val_loss += loss.item()
            
            # Direction Accuracy
            # Ignore small movements (< 0.1%)
            meaningful_mask = torch.abs(batch_y) > 0.001
            if meaningful_mask.sum() > 0:
                pred_sign = torch.sign(predicted[meaningful_mask])
                true_sign = torch.sign(batch_y[meaningful_mask])
                correct = (pred_sign == true_sign).float().sum()
                correct_direction += correct
                total_val += meaningful_mask.sum()
        
        avg_val_loss = val_loss / ((len(X_val) + batch_size - 1) // batch_size)
        val_acc = correct_direction / (total_val + 1e-9)
    
    print(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.6f} | Val Loss: {avg_val_loss:.6f} | Dir Acc: {val_acc:.1%}")

print("\n✅ 조련 완료!")

# 7. 모델 저장
BRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
torch.save(brain.state_dict(), BRAIN_FILE)
print(f"\n💾 훈련된 모델 저장: {BRAIN_FILE}")

# 8. 자원 정리 (VRAM Cleanup)는 스크립트 맨 마지막에 수행
print("\n🧹 시스템 정리 중...")
# 먼저 brain 사용 후 정리
del X, y, X_train, y_train, X_val, y_val, t_closes, t_volumes
del brain, optimizer
torch.cuda.empty_cache()
print("   - VRAM 데이터 소거 완료")
print("=" * 60)

# (성능 검증 코드는 위 훈련 루프에서 이미 수행됨)
print("✅ 모든 프로세스 완료.")

print("\n" + "=" * 60)
print("🎓 OSS가 훈련되었습니다. 백테스트를 시작하세요.")

# VRAM Cleanup at the VERY END
print("\n🧹 시스템 정리 중...")
try:
    del X, y, X_train, y_train, X_val, y_val, t_closes, t_volumes
    del brain, optimizer
except:
    pass
torch.cuda.empty_cache()
print("   - VRAM 데이터 소거 완료")
print("=" * 60)
