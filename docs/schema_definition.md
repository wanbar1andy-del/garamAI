# GARAM Pipeline Data Schema V2 (SSOT: core/contracts)

본 문서는 파이프라인 각 Stage 간 데이터 입출력 규격을 정의한다.
단, **SSOT(단일 진실원천)는 문서가 아니라 코드**이며, 본 문서는 코드를 “설명/운영 가이드”로 요약한 2차 산출물이다.

## SSOT 원칙

- 스키마의 최종 정의(SSOT): `core/contracts/`
  - `core/contracts/universe.py`  → UniverseRow
  - `core/contracts/market.py`    → MarketSchema
  - `core/contracts/features.py`  → FeatureFrameSpec
  - `core/contracts/signals.py`   → SignalRecord
  - `core/contracts/hero.py`      → HeroMetadata
  - `core/contracts/allocation.py`→ AllocationRow
- 본 문서의 모든 필드/타입/의미는 위 Contracts 코드와 충돌할 수 없으며,
  충돌 시 **코드가 우선**한다.
- 스키마 변경은 V3 문서 생성 후 마이그레이션(또는 Backward-compatible 확장) 원칙을 따른다.

---

## 0. 공통 규칙 (Stage 공통)

### Symbol 규칙

- 종목코드 `symbol`은 **문자열 6자리 0-padding**을 기본 규약으로 한다.
- 모든 Stage의 I/O는 `symbol`을 이 규약으로 통일한다.

### Timestamp 규칙

- 원시 CSV는 `date`(YYYYMMDDHHMMSS) 문자열 기반을 허용한다.
- 내부 표준은 `timestamp`(datetime-like)로 통일하되, 변환/타임존 규칙은 MarketSchema에 따른다.

---

## 1. INGEST (수집) → VALIDATE (검증)

### Format

- CSV File: `{symbol}.csv` 또는 `{symbol}_1m.csv` (프로젝트 내 파일명은 현존 체계 존중)
- Ingest 단계는 원시 데이터 보존이 목적이며, 검증/보정은 Validate 단계에서 수행한다.

### Required Columns (Raw)

- `date` (String, YYYYMMDDHHMMSS): 체결시간 (PK 성격)
- `open` (Int)
- `high` (Int)
- `low` (Int)
- `close` (Int)
- `volume` (Int)

### Notes

- 누락/중복/비정상 값은 Validate 단계에서 `is_filled`, `is_outlier` 등 태그로 기록 가능

---

## 2. VALIDATE (검증) → STORE (저장)

### Format

- Cleaned CSV 또는 Parquet (캐시/성능 목적)
- 저장 계층은 “원본과 정제본”을 분리 가능하나, Schema는 동일하게 유지한다.

### Required Columns

- 1번과 동일 (OHLCV + date/timestamp)

### Optional Tag Columns (허용)

- `is_filled` (Boolean): 결측치 보간 여부
- `is_outlier` (Boolean): 이상치 여부
- 기타 태그는 `tag_*` 네임스페이스 권장

---

## 3. STORE (저장) → FEATURE (지표)

### Format

- DataFrame(In-memory) 또는 Cache(Parquet 등)

### Contract Reference

- SSOT: `core/contracts/market.py::MarketSchema`
- Feature 입력은 “시장 데이터(OHLCV + 시간)”가 기준이며, 타임존/중복 인덱스 허용 여부는 Gate/Schema 정책을 따른다.

---

## 4. FEATURE (지표) → SIGNAL (전략)

### Format

- DataFrame(In-memory) 또는 Cache

### Required Core Fields

- `timestamp`
- `symbol`
- `close`

### Indicator Fields (예시)

- `ma_20`
- `rsi_14`
- `vol_ratio`

### Contract Reference

- SSOT: `core/contracts/features.py::FeatureFrameSpec`
- “어떤 지표가 필수인지/검증 규칙”은 FeatureFrameSpec가 결정한다.
- 문서의 지표 리스트는 예시이며, 실제 필수 지표는 코드 기준으로 판단한다.

---

## 5. SIGNAL (전략) → HERO / SCAN (발굴)

### Format

- Hero scan 결과는 `HeroMetadata` 리스트(또는 CSV export)로 표현한다.

### Contract Reference (SSOT)

- `core/contracts/hero.py::HeroMetadata`

예시 (문서용 요약):

```python
@dataclass
class HeroMetadata:
    symbol: str
    is_hero: bool
    hero_score: float
    expectancy_net: float
    win_rate: float
    trades: int
    overnight_tier: str  # STRICT, SOFT, NONE
    meta: Optional[Dict[str, float]] = None
```

## 6. HERO (발굴 결과) → CAPITAL_POLICY (배분)

### Format

- Allocation plan은 DataFrame/CSV로 출력 가능

### Contract Reference (SSOT)

- `core/contracts/allocation.py::AllocationRow`

### 필수 컬럼(요약)

- `symbol`
- `sleeve` (ALPHA/RESERVE 등)
- `tier` (STRICT/SOFT/INTRADAY/NONE 등)
- `weight` (0~1)
- `notional` (금액)
- `reason` (설명)

### 정책 규약

- **No Hero = No Trade** (Alpha allocation = 0) 는 시스템 규약(Contract 수준)으로 유지한다.

---

## Change Management

- **필드 추가**: Backward-compatible 확장 권장
- **필드 삭제/의미 변경**: V3 문서 생성 + 마이그레이션 스텝 필수
- **문서/코드 충돌 발견 시**: **코드(Contracts) 우선**, 문서 즉시 수정
