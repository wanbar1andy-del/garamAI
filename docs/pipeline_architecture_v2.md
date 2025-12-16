# 가람(GARAM) 이상적인 파이프라인 아키텍처 V2

## 1. 파이프라인 6단계 구조

가람 시스템은 데이터 흐름의 명확성을 위해 다음 6단계로 구성된다. 각 단계는 단방향(Top-Down/Sequential)으로 흐르며 역참조를 금지한다.

### 1-1. INGEST (데이터 수집)

- **역할**: 거래소/데이터소스 API에서 원천 데이터를 "있는 그대로" 수집.
- **규칙**:
  - 지표 계산, 전략 판단 금지.
  - 오직 API 호출 -> Raw 저장/통일 포맷 저장만 수행.
- **출력 계약**: `timestamp, open, high, low, close, volume, exchange, symbol` (최소 필수)

### 1-2. VALIDATE & CLEAN (검증 및 정제)

- **역할**: 수집된 데이터의 무결성 검사, 이상치/결측치 처리.
- **규칙**:
  - 검사 항목 명문화 (타임스탬프 연속성, 가격 음수 체크 등).
  - 처리 정책 저장 (결측 보간 or 제외).
- **출력**: `cleaned_data` (is_outlier, is_filled 등 메타 태그 포함 가능)

### 1-3. STORE (저장 및 관리)

- **역할**: 정제된 데이터를 중앙에서 관리 및 제공.
- **규칙**:
  - 파일/DB 구조 고정 (예: `data/cleaned/YYYY/MM/DD.parquet`).
  - 버전 관리 도입 (Schema V1, V2...).
  - **모든 하위 단계(Feature, Signal 등)는 오직 STORE를 통해서만 데이터를 읽는다.**

### 1-4. FEATURE (지표 및 팩터)

- **역할**: 전략 공용 지표 식/팩터 계산.
- **규칙**:
  - 지표 정의의 중앙화 (`features/technical.py`).
  - 전략별 중복 계산 제거.
- **출력**: `timestamp` + `price` + `factor_*` 테이블.

### 1-5. SIGNAL & EXECUTION (전략 및 실행)

- **역할**: Feature 데이터를 받아 매수/매도 시그널 생성 및 주문 집행.
- **구조**:
  - **전략(Signal)**: Input(Feature) -> Logic -> Output(Signal Table).
  - **실행(Execution)**: Input(Signal) -> Exchange API -> Order Log.
- **규칙**: 전략 로직과 실행 로직의 완전한 분리. 리스크 관리 모듈 필수 포함.

### 1-6. MONITOR & LOG (모니터링)

- **역할**: 전체 파이프라인 상태 감시 및 성과 리포팅.
- **규칙**:
  - 로그 포맷 통일 (Time, Stage, Level, Msg).
  - 에러 발생 시 즉시 알림 정책.
  - 일별 PnL 표준 리포트 생성.

---

## 2. 작업 로드맵

### Phase 1: 인벤토리 & 시각화

- 현재 존재하는 모든 스크립트/문서 목록화.
- 각 파일의 역할 및 현재 파이프라인 단계 매핑.
- 데이터 흐름 시각화 (AS-IS).

### Phase 2: 구조 재설계 (TO-BE)

- 6단계 타겟 구조 확정.
- 각 단계별 입출력 스키마 정의.
- 폴더 구조 재정의 (`/pipeline/01_ingest`, `/pipeline/02_validate` ...).

### Phase 3: 리팩토링 및 이관

- **INGEST**: 기존 수집기(`kiwoom_login_ui.py` 등) 정리 및 이동.
- **VALIDATE**: 무결성 검사 스크립트 통합.
- **FEATURE/SIGNAL**: 백테스트/라이브 로직 분리.

### Phase 4: 안정화 (Error Handling)

- 공통 에러 핸들러 도입.
- 재시도/알림 로직 표준화.

### Phase 5: 문서화

- `docs/` 폴더 내 최신화.
- 구버전 아카이브.
