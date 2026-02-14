# Champion Hero Strategy: Operational SSOT Checklist (2/5/0 Rule)

**"히어로 실체화"를 위한 1장짜리 운영 매뉴얼**

## 1. Pre-Open (08:30 ~ 장 시작 전)

- [ ] **Universe Sync**: 401개 종목 유니버스 최신화 (`sync_universe`)
- [ ] **Data Audit**: 어제자 데이터 정합성 검증 (`audit_data_quality_1y`)
- [ ] **State Check**: 잔고/미체결 확인 및 프로그램/API 접속 상태 점검
- [ ] **Veto Calculation (Daily)**: 전일 종가 기준 B-Filter 선계산
  - `Vol_Accel` = ATR(5) / ATR(60) > 1.5 → **VETO** (진입 불가)
  - `ATR%` = ATR(20) / Close * 100 > 10% → **VETO** (진입 불가)
  - `Regime` = Index MA20 하회 & Vol 폭주 시 → **HALF or OFF**

## 2. Market Open & ORB (장 시작 ~ 앵커 시점)

- [ ] **ORB Logging**: 장 시작 후 초반(15분/30분) 고가(High)/저가(Low) 기록
- [ ] **Intraday Ignition**: 초반 거래량/변동성 강도 확인 (`fs_fast`)
- [ ] **No Trade Zone**: ORB 기준이 형성되기 전까지 진입 금지 (원칙)

## 3. Hero Selection & Entry (진입 판단 트리거)

- [ ] **Champion Score Calculation**:
  - `Score` = f(ORB_Breakout, fs_fast, fm_daily_trend)
  - `fm_daily_trend`: 일봉상 상승 추세 (정배열/모멘텀)
  - `ORB_Breakout`: 현재가 > ORB_High (돌파 확인)
- [ ] **Filtering (Veto Only)**:
  - `expectancy_net` (과거 통계)는 **참고용**일 뿐, **Veto하지 않음**.
  - 오직 `Vol_Accel > 1.5` 또는 `ATR% > 10%` 인 경우만 **DROP**.
- [ ] **2/5/0 Allocation (신호 강도 기반 배분)**:
  - **K=2 (Strong)**: Top1, Top2 점수가 모두 높고(`T_STRONG`), 격차가 명확할 때 → **각 50%**
  - **K=5 (Weak)**: 점수는 통과했으나(`T_WEAK`), 압도적이지 않을 때 → **각 20%**
  - **K=0 (Rest)**: 후보가 없거나 점수 미달 시 → **ALL CASH (휴식)**
  - **LOG**: "K=2 (Strong), Weight 0.5" 또는 "K=0 (No Signal)"

## 4. Monitoring & Management (장중 대응)

- [ ] **Stop Loss (Fail-Fast)**:
  - `-3% ~ -4%`: **WARNING** (주시/비중축소 고려)
  - `-5%`: **KILL** (즉시 청산 & 당일 재진입 금지)
- [ ] **Time Cut (유통기한)**:
  - 진입 후 16봉(약 4시간) 경과 시 수익 부진하면 정리 (스캔/설정에 따름)
- [ ] **Hero Death (급변동)**:
  - `Vol_Accel ≥ 1.8` AND (이평 이탈 등 기술적 붕괴) → **IMMEDIATE EXIT**
  - **LOG**: "변동성 폭발로 인한 사망 판정 → **EXIT/ROTATE**"

## 5. EOD & Overnight (장 마감 ~ )

- [ ] **Overnight Decision**:
  - 원칙: **Allow** (별도 Regime Ban 없을 시)
  - 히어로 지위 유지 시 오버나잇 (다음날 갭 상승 기대)
- [ ] **Review**: 당일 `Champion Score`, `K` 결정 사유, 청산 로그 기록 (`HeroDiary`)
- [ ] **Preparation**: 내일을 위한 ORB 기준 및 Veto 지표 갱신
