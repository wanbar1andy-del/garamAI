# GARAM DGE Portfolio KPI 정의

**버전**: v1.1  
**날짜**: 2025-11-26  
**목표**: 하루 +0.4% 성장을 위한 포트폴리오 레벨 KPI

---

## 📊 핵심 KPI (4대 지표)

### 1. Portfolio CAGR ≥ 60%

**측정 방법**: 연환산 수익률 (Compound Annual Growth Rate)

**판단 기준**:

- ✅ **Target**: 60% 이상
- ⚠️ **Warning**: 40–60%
- ❌ **Fail**: 40% 미만

**계산식**:

```
일일 성장률 g = 0.004 (0.4%)
연간 거래일 = 250일
CAGR = (1 + g)^250 - 1 ≈ 170% (이론값)

실제 목표 = 60% (보수적 달성 가능 목표)
```

### 2. Max DD ≤ 25%

**측정 방법**: 최대 낙폭 (Maximum Drawdown)

**판단 기준**:

- ✅ **Excellent**: DD ≤ 15%
- ✅ **Good**: DD ≤ 25%
- ⚠️ **Warning**: DD 25–35%
- ❌ **Fail**: DD > 35%

**이유**:

- 일일 리스크 5% × 5일 연속 손실 = 25% 근접
- Kelly Fraction 0.25 적용 시 허용 가능한 범위

### 3. Capital Efficiency ≥ 2.0

**핵심 혁신 지표**: 단위 자본당 수익 생산성

**측정 방법**:

```
Capital Efficiency = CAGR / Avg Gross Exposure
```

**판단 기준**:

- 🌟 **Excellent**: ≥ 4.0 (자본을 극소로 쓰면서 높은 수익)
- ✅ **Good**: 2.0–4.0
- ⚠️ **Warning**: 1.0–2.0 (자본을 많이 쓰지만 효율 낮음)
- ❌ **Fail**: < 1.0 (전략 재검토 필요)

**해석 예시**:

| CAGR | Avg Exposure | Efficiency | 해석 |
|------|--------------|------------|------|
| 60% | 10% | **6.0** | 전략 우수, 자본 활용도 낮음 → 심볼/전략 확장 가능 |
| 60% | 30% | **2.0** | Balanced, 목표 달성 |
| 60% | 80% | **0.75** | 자본 과다 사용, 전략 효율 낮음 → 재검토 |
| 120% | 60% | **2.0** | 높은 수익이지만 자본 의존적 |

**전략적 의사결정**:

- Efficiency > 4.0 → **스케일 업** (더 많은 심볼/전략 추가)
- Efficiency 2.0–4.0 → **유지** (현재 배분 적정)
- Efficiency < 2.0 → **최적화 또는 교체**

### 4. 일평균 노출 30–60%

**측정 방법**: Average Daily Gross Exposure

**판단 기준**:

- ✅ **Ideal Range**: 30–60%
- ⚠️ **Too Conservative**: < 20% (자본 활용 부족)
- ⚠️ **Too Aggressive**: > 80% (집중 리스크)

**이유**:

- 30% 미만: 자본 낭비, 기회비용 발생
- 60% 초과: 단일 이벤트(시장 급락 등)에 과도 노출

---

## 📈 보조 지표

### Risk-Adjusted Metrics

**Sharpe Ratio**:

- Target: ≥ 1.5
- Excellent: ≥ 2.0

**Calmar Ratio** (CAGR / Max DD):

- Target: ≥ 2.0
- Excellent: ≥ 3.0

**Risk Utilization**:

```
Risk Utilization = 실제 사용된 위험 / Risk Budget
Target: 60–80%
```

### Operational Metrics

**평균 동시 포지션 수**:

- Target: 3–8개
- 이유: 분산 효과 + 관리 가능성

**거래 빈도**:

- DGE 모드: 연 50–100회 이상 (통계적 유의성)
- Intraday: 더 높은 빈도 가능

**Win Rate**:

- Target: 40–55%
- Payoff Ratio (R:R): ≥ 2.0

---

## 🎯 케이스 스터디: KPI 해석 방법

### Case A: **확장 가능한 우수 전략**

```
Portfolio CAGR: 60%        ✅
Max DD: 18%                ✅
Capital Efficiency: 5.0    🌟
Avg Exposure: 12%          ⚠️ (낮음)
```

**해석**:

- 전략의 단위 리스크당 알파가 매우 강함
- 자본 활용도가 낮아 성장 여지 큼

**Action**:

1. Top10 → Top20으로 심볼 확장
2. 전략 추가 (ORB + VWAP + Swing)
3. Exposure cap 10% → 30% 상향

**예상 결과**:

- CAGR 60% → 120–150%
- Avg Exposure 12% → 36%
- Capital Efficiency 유지 (~4.0)

---

### Case B: **효율 개선 필요**

```
Portfolio CAGR: 40%        ⚠️
Max DD: 28%                ⚠️
Capital Efficiency: 0.5    ❌
Avg Exposure: 80%          ⚠️ (과다)
```

**해석**:

- 자본을 많이 쓰지만 수익률 낮음
- 리스크 대비 효율 매우 낮음

**Action**:

1. 전략 재검토 (WFO 최적화, 필터 강화)
2. Dead symbol 제거 강화
3. Kelly fraction 축소 또는 전략 교체
4. Exposure cap 축소 (80% → 50%)

**목표**:

- Efficiency 0.5 → 2.0 이상으로 개선
- Max DD 축소

---

### Case C: **Balanced (이상적)**

```
Portfolio CAGR: 80%        🌟
Max DD: 20%                ✅
Capital Efficiency: 2.5    ✅
Avg Exposure: 32%          ✅
```

**해석**:

- 모든 KPI가 목표 범위 내
- 안정적인 포트폴리오 운영 중

**Action**:

- 현재 배분 유지
- 정기 모니터링 (월 1회 KPI 체크)
- 신규 전략은 소규모로 추가 테스트

---

## 🔄 KPI 측정 주기

| 지표 | 측정 주기 | 보고 위치 |
|------|-----------|-----------|
| CAGR | 주간 | Regime Lab Dashboard |
| Max DD | 실시간 | Risk Summary Panel |
| Capital Efficiency | 주간 | Portfolio Report |
| Avg Exposure | 일일 | GaramUI Overview |
| Sharpe Ratio | 월간 | Monthly Report |

---

## 📋 KPI 달성 체크리스트

### Daily (일일)

- [ ] 금일 Gross Exposure 확인
- [ ] Kill Switch 활성화 여부 (Max Daily Loss 5%)
- [ ] 포지션 수 확인 (3–8개 범위)

### Weekly (주간)

- [ ] 주간 CAGR 계산
- [ ] Capital Efficiency 계산
- [ ] Dead Symbol 제거 및 Top10 갱신

### Monthly (월간)

- [ ] 4대 KPI 종합 평가
- [ ] Sharpe, Calmar Ratio 계산
- [ ] WFO Re-optimization (필요 시)
- [ ] 전략 추가/교체 검토

---

## 🚀 KPI 기반 의사결정 플로우

```
1. 주간 KPI 측정
   ↓
2. Capital Efficiency 체크
   ↓
   ├─ Efficiency > 4.0? → 스케일 업 (심볼/전략 확장)
   ├─ Efficiency 2.0–4.0? → 유지
   └─ Efficiency < 2.0? → 최적화 또는 교체
   ↓
3. CAGR & DD 체크
   ↓
   ├─ CAGR ≥ 60% AND DD ≤ 25%? → ✅ 목표 달성
   ├─ CAGR < 60% BUT Efficiency > 4.0? → 스케일 업
   └─ DD > 25%? → Risk Budget 축소
   ↓
4. 다음 주 운영 방향 결정
```

---

## 📌 요약: 한 줄 KPI

```
DGE 포트폴리오 목표:
- Portfolio CAGR ≥ 60%
- Max DD ≤ 25%
- Capital Efficiency ≥ 2.0
- 일평균 노출 30–60%
```

이 4개 숫자로 모든 전략·튜닝·WFO 결과를 빠르게 평가합니다.

---

## 🔗 관련 문서

- [DGE Risk Module](file:///c:/garam/garam/risk/dge.py)
- [Portfolio Analyzer](file:///c:/garam/garam/scripts/analyze_portfolio_efficiency.py) (생성 예정)
- [Top10 Universe Selector](file:///c:/garam/garam/scripts/select_top10_universe.py) (생성 예정)
- [Implementation Plan](file:///C:/Users/wanba/.gemini/antigravity/brain/697c06a2-09de-4a67-abb1-863512b5be38/implementation_plan.md)
