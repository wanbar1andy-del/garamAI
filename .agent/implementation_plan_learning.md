# OSS 자율 학습 시스템 구현 계획

## 핵심 개념
OSS가 **스스로** 학습하도록 신경망을 실시간으로 훈련

## 구현 단계

### 1. 신경망 학습 준비
- `brain.train()` 모드 활성화
- Optimizer 추가 (Adam)
- Loss function 정의: MSE(predicted_pnl, actual_pnl)

### 2. 실시간 학습 사이클
```
거래 진입 → 예측 저장
거래 종료 → 실제 pnl 계산
신경망에 피드백 → loss.backward()
가중치 업데이트 → optimizer.step()
```

### 3. 학습 데이터
- Input: RSI, Volume, Whale, Squeeze 등
- Output: 예측 수익률
- Label: 실제 거래 수익률

### 4. 즉시 반영
- 매 거래마다 신경망 업데이트
- 다음 거래에 즉시 반영
- 주기적으로 모델 저장

## 기대 효과
- OSS가 스스로 최적 전략 발견
- 시장 변화에 자동 적응
- 내가 개입하지 않아도 계속 진화
