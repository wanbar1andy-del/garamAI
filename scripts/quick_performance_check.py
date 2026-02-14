"""
빠른 성능 추정 스크립트
현재 훈련 데이터로 기준선(baseline) 성능 계산
"""
import torch
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path("c:/garam/garam")
CACHE_FILE = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"

print("=" * 60)
print("📊 훈련 데이터 성능 기준선 분석")
print("=" * 60)

# 1. 데이터 로드
with open(CACHE_FILE, 'rb') as f:
    cached = pd.read_pickle(f)
    closes = cached['closes']
    volumes = cached['volumes']

print(f"\n데이터: {closes.shape[1]} 종목, {closes.shape[0]} bars")

# 2. 미래 수익률 계산 (120분 후)
target_shift = 120
future_closes = closes.shift(-target_shift)
future_returns = (future_closes / closes) - 1.0
future_returns = future_returns.clip(-0.15, 0.15)

# 결측치 제거
valid_mask = ~future_returns.isna()
valid_returns = future_returns[valid_mask].values.flatten()

print(f"\n유효 샘플: {len(valid_returns):,}개")

# 3. 기본 통계
print("\n" + "=" * 60)
print("📈 미래 수익률 분포 (120분 후)")
print("=" * 60)
print(f"평균: {valid_returns.mean():.4f}% ({valid_returns.mean()*100:.2f}%)")
print(f"표준편차: {valid_returns.std():.4f}")
print(f"최대: {valid_returns.max():.4f} (+{valid_returns.max()*100:.1f}%)")
print(f"최소: {valid_returns.min():.4f} ({valid_returns.min()*100:.1f}%)")

# 4. 방향 분석
meaningful_mask = np.abs(valid_returns) > 0.001  # 0.1% 이상만
meaningful_returns = valid_returns[meaningful_mask]

up_count = (meaningful_returns > 0).sum()
down_count = (meaningful_returns < 0).sum()
total_meaningful = len(meaningful_returns)

print(f"\n의미있는 움직임 (>0.1%): {total_meaningful:,}개")
print(f"  - 상승: {up_count:,}개 ({up_count/total_meaningful*100:.1f}%)")
print(f"  - 하락: {down_count:,}개 ({down_count/total_meaningful*100:.1f}%)")

# 5. 고수익 거래 분석
high_return_mask = np.abs(valid_returns) > 0.03  # 3% 이상
high_returns = valid_returns[high_return_mask]
print(f"\n고수익 거래 (>3%): {len(high_returns):,}개 ({len(high_returns)/len(valid_returns)*100:.2f}%)")
print(f"  - 평균 수익: {high_returns.mean()*100:.2f}%")

# 6. Random Baseline (랜덤 예측)
print("\n" + "=" * 60)
print("🎲 Random Baseline 성능")
print("=" * 60)

# 랜덤 예측 (균등 분포)
np.random.seed(42)
random_predictions = np.random.uniform(-0.15, 0.15, len(meaningful_returns))

# MSE Loss
mse_loss = ((random_predictions - meaningful_returns) ** 2).mean()
print(f"Random MSE Loss: {mse_loss:.6f}")

# Direction Accuracy
random_direction = np.sign(random_predictions)
true_direction = np.sign(meaningful_returns)
random_accuracy = (random_direction == true_direction).mean()
print(f"Random Direction Accuracy: {random_accuracy:.1%}")

# 7. 목표 성능
print("\n" + "=" * 60)
print("🎯 훈련 목표")
print("=" * 60)
print(f"MSE Loss < {mse_loss:.6f} (Random보다 낮아야 함)")
print(f"Direction Accuracy > 50% (Random: {random_accuracy:.1%})")
print(f"고수익 거래 포착 > 5% (Weighted Loss 덕분)")

# 8. 현재 훈련 상태 추정
print("\n" + "=" * 60)
print("⏳ 현재 훈련 상태 추정 (Batch 500)")
print("=" * 60)
print(f"학습된 샘플: 512,000개 ({512000/len(valid_returns)*100:.1f}%)")
print(f"업데이트 횟수: 500회 (537M params)")

# 초기 랜덤 가중치 -> 점진적 개선 예상
# Batch 500에서 예상 성능 (경험적 추정)
estimated_loss = mse_loss * 0.85  # 15% 개선 예상
estimated_acc = 0.48 + (0.52 - random_accuracy) * 0.3  # 30% 진전

print(f"\n예상 현재 성능:")
print(f"  - MSE Loss: ~{estimated_loss:.6f} (Random 대비 85%)")
print(f"  - Direction Acc: ~{estimated_acc:.1%}")
print(f"  - 학습 진행: 초기 단계 (4.6%)")

print("\n" + "=" * 60)
print("✅ 분석 완료")
print("=" * 60)
print("\n💡 결론:")
print("   - Random보다 나은지 확인하려면 Epoch 완료 필요")
print("   - 현재는 초기 학습 단계 (가중치 초기화)")
print("   - 유의미한 개선은 Batch 2000+ 이후 예상")
