# GARAM Advanced Risk & Regime Specification

**버전**: v1.0  
**날짜**: 2025-11-26  
**목표**: 단순 가격 하락이 아닌 "시장 컨텍스트(HeatScore)"에 기반한 동적 리스크 관리 및 자본 배분 시스템 설계

---

## 1. HeatScore Engine (시장 공격성 지수)

단기 시장의 "체질"과 "수급 에너지"를 정량화하여 DGE의 공격성을 조절하는 핵심 모듈.

### 1.1 입력 변수 (Inputs)

| 변수명 | 설명 | 소스 | 윈도우 | 가중치(w) |
|--------|------|------|--------|-----------|
| **ForeignFlow_Z** | 외국인 KOSPI200 순매수 강도 | Kiwoom (일별 집계) | 20일 Z-score | 0.5 |
| **FX_Stability_Z** | USD/KRW 환율 안정성 (역상관) | Kiwoom/Yahoo | 20일 Z-score (Reverse) | 0.3 |
| **Volatility_Z** | 변동성 안정성 (낮을수록 좋음) | ATR / VKOSPI | 20일 Z-score (Reverse) | 0.2 |

*Note: FX와 Volatility는 값이 오르면(환율 급등, 변동성 확대) 시장에 부정적이므로 역산(-Z)하여 적용.*

### 1.2 계산 로직 (Calculation)

```python
def calculate_heat_score(flow, fx, vol):
    # 1. Normalize (Z-score)
    z_flow = (flow.current - flow.mean_20d) / flow.std_20d
    z_fx = -1 * (fx.current - fx.mean_20d) / fx.std_20d  # 환율 급등 = 악재
    z_vol = -1 * (vol.current - vol.mean_20d) / vol.std_20d # 변동성 확대 = 악재

    # 2. Weighted Sum
    raw_score = (0.5 * z_flow) + (0.3 * z_fx) + (0.2 * z_vol)
    
    # 3. Clipping (-2.0 ~ +2.0)
    heat_score = max(-2.0, min(2.0, raw_score))
    
    return heat_score
```

### 1.3 출력 및 해석 (Output Interpretation)

| HeatScore 구간 | 모드 (Mode) | DGE Multiplier | 행동 지침 |
|----------------|-------------|----------------|-----------|
| **> +0.7** | 🔥 **Bull / Aggressive** | **1.2x ~ 1.5x** | 리스크 확대, 동시 포지션 수 증가, 추격 매수 허용 |
| **-0.7 ~ +0.7** | ⚖️ **Neutral** | **1.0x** | 기본 룰 적용 (Standard DGE) |
| **< -0.7** | ❄️ **Bear / Defensive** | **0.5x ~ 0.0x** | 신규 롱 금지, 숏/헤지 위주, 타이트한 익절 |

---

## 2. Context-Aware Risk Manager (2% 룰 재해석)

"-2% 하락"을 무조건적인 손절 신호가 아닌, "컨텍스트 확인 신호"로 처리하는 의사결정 트리.

### 2.1 의사결정 트리 (Decision Tree)

**Trigger**: KOSPI/Symbol Daily Drop > 2.0% (or > 1.5 * ATR)

1. **Check Structural Trend (구조적 추세)**
    * `IF` MA_60 > MA_120 `AND` HeatScore > -0.5:
        * **판단**: 📈 **Dip in Bull (상승장 속 조정)**
        * **Action**:
            * Core: 유지 (Hold) 또는 저점 매수 (Buy Dip)
            * DGE: 15분/1H 모멘텀 반전 시 공격적 단기 롱 진입
    * `ELSE`:
        * **판단**: 📉 **Structural Weakness (구조적 하락)**
        * **Action**:
            * Core: 리스크 관리 (Hedge or Reduce)
            * DGE: 롱 금지, 숏 시그널만 허용

2. **Check Intraday Noise (일중 노이즈)**
    * `IF` Drop < 1.0 * ATR (평균적인 변동폭 이내):
        * **판단**: 🌊 **Normal Noise**
        * **Action**: 기존 로직 유지 (손절은 기술적 레벨에서만 수행)

### 2.2 손절/익절 로직 개선

* **Hard Stop**: -2% 고정값 폐지.
* **Dynamic Stop**: `Entry Price - (ATR_14d * k)`
  * HeatScore > 0.7 (Bull): k = 2.0 (여유 있게)
  * HeatScore < -0.7 (Bear): k = 1.0 (타이트하게)

---

## 3. Core + Overlay Capital Allocation

자본을 "지키는 돈(Core)"과 "버는 돈(Overlay)"으로 분리하여 운용.

### 3.1 자본 배분 구조

| Book Type | 비중 (Target) | 역할 | 운용 전략 |
|-----------|---------------|------|-----------|
| **Core Book** | **40% ~ 60%** | 베타 노출, 장기 추세 추종 | ETF, 대형주 현물 (저회전) |
| **Overlay Book** | **0% ~ 50%** | 알파 창출, 일일 수익 | **DGE Strategies** (고회전) |
| **Cash Buffer** | **10% ~ 20%** | 유동성 확보, 긴급 대응 | 현금, 초단기 채권 |

### 3.2 동적 배분 룰 (Dynamic Allocation Rule)

Overlay Book(DGE)의 자본 할당량(`Allocated_Capital`)은 HeatScore에 따라 매일 아침 조정.

```python
def allocate_capital(total_equity, heat_score):
    base_overlay_ratio = 0.30 (30%)
    
    # HeatScore에 따른 조정 (-2.0 ~ +2.0)
    # Score +2.0 -> Ratio +20%p (Total 50%)
    # Score -2.0 -> Ratio -20%p (Total 10%)
    adjustment = heat_score * 0.10 
    
    target_overlay_ratio = base_overlay_ratio + adjustment
    target_overlay_ratio = max(0.0, min(0.50, target_overlay_ratio)) # Cap 0~50%
    
    return total_equity * target_overlay_ratio
```

---

## 4. Small Wave Filter (비용 효율성 필터)

"먹을 게 없는 파도"는 수수료만 나가므로 진입 자체를 차단.

### 4.1 필터 로직

* **Cost Threshold**: 0.25% (수수료 0.015% * 2 + 세금 0.18% + 슬리피지 0.04%)
* **Minimum R (Reward)**: Cost * 3.0 = **0.75%**

**Rule**:

```python
expected_range = ATR_14d * volatility_ratio  # 또는 ORB High - Low
if expected_range < 0.75%:
    return SIGNAL_SKIP  # "파도가 너무 작음"
```

---

## 5. 구현 로드맵 (Implementation Roadmap)

### Phase 2.5: Advanced Risk Module

1. **Data Feed 확장**:
    * 외국인 수급, 환율 데이터 수집 파이프라인 구축 (`fetch_market_context.py`)
2. **HeatScore 구현**:
    * `risk/heat_score.py` 모듈 작성
    * RegimeRouter에 통합
3. **DGE 연동**:
    * `DailyGrowthEngine`에 `heat_score` 파라미터 수용
    * Position Sizing 시 Multiplier 적용
4. **Backtest 검증**:
    * 기존 DGE 전략에 HeatScore 필터 적용 전/후 성과 비교 (CAGR, MDD)

---

## 6. 기대 효과

1. **수익률 질적 개선**: "나쁜 날"의 손실을 줄이고 "좋은 날"의 수익을 극대화하여 Sharpe Ratio 상승.
2. **심리적 안정**: -2% 하락 시 기계적 손절이 아니라, "구조적 하락 vs 조정"을 구분하여 뇌동매매 방지.
3. **비용 절감**: 기대 수익이 낮은 날의 무의미한 매매를 필터링하여 수수료/세금 절감.
