# GARAM Acceleration Mechanisms: The Physics of Profit

**버전**: v1.0  
**날짜**: 2025-11-26  
**목표**: 단순한 타이밍(Timing)을 넘어, 수익을 폭발시키는 물리적/구조적 메커니즘(Mechanism) 정의 및 구현 설계

---

## 1. 서론: 가속(Acceleration)이란 무엇인가?

GARAM에서 정의하는 가속은 **"최소한의 리스크(연료)로 최대한의 가격 변동(거리)을 최단 시간(시간)에 만들어내는 현상"**입니다.
이는 뉴턴의 제2법칙($F=ma$)과 유사하게, 시장의 **불균형 에너지(Force)**가 가격의 **관성(Mass)**을 이겨내고 **속도 변화(Acceleration)**를 만드는 과정입니다.

우리는 이 가속을 만들어내는 3가지 핵심 엔진을 정의하고, 이를 전략화합니다.

---

## 2. Mechanism 1: Volatility Compression (변동성 압축 폭발)

**"스프링 효과"**: 눌린 에너지는 반드시 튀어 오른다.

### 2.1 에너지원 (Source)

* 시장 참여자들의 관망, 눈치 보기, 혹은 에너지가 한쪽으로 쏠리기 전의 평형 상태.
* 가격이 좁은 박스권(Range)에 갇혀 변동성이 극도로 낮아진 상태.

### 2.2 메커니즘 (Physics)

1. **Compression**: 가격 변동폭이 줄어들며(NR4/NR7, BB Squeeze) 에너지가 응축됨.
2. **Trigger**: 뉴스, 수급, 혹은 단순한 기술적 돌파로 인해 평형이 깨짐.
3. **Expansion**: 응축된 에너지가 한 방향으로 분출되며 평소의 2~3배 이상의 장대 양봉/음봉 출현.

### 2.3 구현 전략 (Strategy: `DGE_VBO`)

* **Setup**:
  * `BandWidth` < 20일 평균의 0.8배 (밴드 수축)
  * `NR7` (최근 7일 중 일중 변동폭이 가장 작음)
* **Action**:
  * 전일 고가(High) 돌파 시 **Buy Stop**.
  * 손절은 전일 저가(Low) 또는 진입가 - 1 ATR.
* **Acceleration Factor**:
  * 이 구간은 "손절은 짧고 익절은 긴" 구간이므로, **Risk Multiplier 1.5x** 적용 가능.

---

## 3. Mechanism 2: Liquidity Vacuum (수급 공백 가속)

**"진공 효과"**: 저항이 없는 곳으로 물체는 빨려 들어간다.

### 3.1 에너지원 (Source)

* 특정 가격대(주요 저항선, 라운드 피겨) 돌파 시 발생하는 매물 공백.
* 공매도 세력의 **Short Squeeze** (급한 환매수) + 추격 매수세(FOMO).

### 3.2 메커니즘 (Physics)

1. **Resistance**: 특정 가격대에 매도 물량이 쌓여 있음.
2. **Breakout**: 강한 매수세가 이 물량을 한입에 잡아먹음(Absorption).
3. **Vacuum**: 그 위 호가창에는 매도 물량이 텅 비어 있음(Air Pocket).
4. **Surge**: 적은 매수세로도 가격이 순식간에 급등.

### 3.3 구현 전략 (Strategy: `DGE_Gap_Drive`)

* **Setup**:
  * 시가(Open)가 주요 저항선 위에서 시작(Gap Up).
  * 초반 5분 거래량이 전일 동시간 대비 200% 이상 폭발.
* **Action**:
  * 시가 또는 5분봉 고가 돌파 시 진입.
  * 익절은 "매도 물량이 다시 두터워지는 지점"까지 홀딩 (Trailing Stop 대신 Target Profit 위주).
* **Acceleration Factor**:
  * **Time Stop**: 30분~1시간 내에 승부가 나지 않으면(가속이 붙지 않으면) 즉시 청산. (시간 가속도 중시)

---

## 4. Mechanism 3: Sector Resonance (섹터 동조화)

**"공명 효과"**: 하나의 파동이 다른 파동을 증폭시킨다.

### 4.1 에너지원 (Source)

* 시장 전체의 자금이 특정 테마/섹터로 쏠리는 쏠림 현상(Herd Behavior).
* 대장주(Leader)의 상승이 2등주, 3등주(Laggard)의 투심을 자극.

### 4.2 메커니즘 (Physics)

1. **Ignition**: 섹터 대장주(예: 삼성전자, 에코프로)가 급등 시작.
2. **Propagation**: 같은 섹터 내 다른 종목들로 매수세 확산.
3. **Resonance**: 섹터 전체가 오르며 시장의 주목을 독점, 매수세가 매수세를 부르는 선순환.

### 4.3 구현 전략 (Strategy: `DGE_Sector_Boost`)

* **Setup**:
  * Top 10 Universe 내 동일 섹터 종목 2개 이상이 동시에 상승 신호 발생.
  * 섹터 지수(KRX 반도체 등)가 시장 지수(KOSPI) 대비 강세(Relative Strength > 0).
* **Action**:
  * 개별 시그널의 신뢰도를 높게 평가하여 진입 장벽(Threshold) 완화.
  * 이미 대장주를 놓쳤다면, 2등주의 눌림목(Pullback) 공략.
* **Acceleration Factor**:
  * **Pyramiding**: 섹터 강세가 확인되면, 수익 중인 포지션에 불타기(Add-on) 허용.

---

## 5. GARAM 통합 설계

이 3가지 메커니즘은 독립적인 전략이 아니라, GARAM의 **DGE 엔진을 가속시키는 터보차저(Turbocharger)**입니다.

### 5.1 통합 구조

```python
class AccelerationEngine:
    def calculate_acceleration(self, symbol, context):
        # 1. Volatility Score (0.0 ~ 1.0)
        vol_score = self._check_compression(symbol)
        
        # 2. Vacuum Score (0.0 ~ 1.0)
        vac_score = self._check_liquidity_vacuum(symbol)
        
        # 3. Resonance Score (0.0 ~ 1.0)
        res_score = self._check_sector_resonance(symbol, context)
        
        # Total Acceleration Factor
        # 하나라도 강력하면 가속, 여러 개 겹치면 폭발
        factor = 1.0 + (vol_score * 0.3) + (vac_score * 0.3) + (res_score * 0.4)
        
        return factor # 1.0 ~ 2.0
```

### 5.2 적용

* **Risk Manager**: `Acceleration Factor`가 높을수록 `Risk Multiplier` 상향 (최대 2.0x).
* **Entry Logic**: `Acceleration Factor`가 높으면 진입 기준(ORB Range 등)을 더 공격적으로 설정.

---

## 6. 결론

우리는 막연히 "오를 것 같아서" 사는 것이 아니라,
**"스프링이 튀어 오르고(Compression), 진공으로 빨려 들어가며(Vacuum), 서로 공명하는(Resonance)"** 물리적 현상에 베팅합니다.

이것이 GARAM이 추구하는 **"구조적 엣지(Structural Edge)"**입니다.
