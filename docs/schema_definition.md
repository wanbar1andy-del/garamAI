# GARAM Pipeline Data Schema V1

본 문서는 파이프라인 각 단계(Stage) 간 데이터 입출력 규격을 정의한다.

## 1. INGEST (수집) -> VALIDATE (검증)

**Format**: CSV File (`symbol_1m.csv`)
**Columns**:

- `date` (String, Format: YYYYMMDDHHMMSS): 체결시간 (PK)
- `open` (Integer): 시가
- `high` (Integer): 고가
- `low` (Integer): 저가
- `close` (Integer): 현재가/종가
- `volume` (Integer): 거래량

## 2. VALIDATE (검증) -> STORE (저장)

**Format**: Cleaned CSV / Parquet
**Columns**: (위와 동일하며, 다음 태그 컬럼 추가 가능)

- `is_filled` (Boolean): 결측치 보간 여부
- `is_outlier` (Boolean): 이상치 여부

## 3. FEATURE (지표) -> SIGNAL (전략)

**Format**: DataFrame (In-Memory) or Cache
**Core**:

- `timestamp`: 기준 시간
- `symbol`: 종목 코드
- `close`: 종가
**Indicators**:
- `ma_20`: 20이동평균
- `rsi_14`: 14 RSI
- `vol_ratio`: 전일 대비 거래량 비율

---
*버전 관리*: 스키마 변경 시 V2 문서 생성 후 마이그레이션 필수.
