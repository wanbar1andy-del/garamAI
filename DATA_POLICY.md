# 데이터 정책

## ⚠️ 절대 규칙

### ✅ 허용: 실제 분 데이터만

- 키움 API로 수집한 1분 데이터
- `g:/내 드라이브/garamdata/history/minute/*.csv`
- 실시간 Kiwoom feed 데이터

### ❌ 금지: Mock/Daily 데이터

- ~~Mock 데이터 생성/사용~~
- ~~Daily (일봉) 데이터~~
- ~~시뮬레이션용 가짜 데이터~~

## 삭제된 항목

### 파일

- `GARAM_Data/history/daily/` (전체 폴더)
- `GARAM_Data/history/*daily*.csv` (12개)
- `logs/daily_backtest_log.csv`
- `scripts/generate_mock_kr_data.py`
- `scripts/verify_live_engine_mock.py`

### 코드 변경 필요

- `run_paper_trading.py`: Mock bar 생성 로직 제거
- 전략 파일: `daily_df` 의존성 제거
- 모든 백테스트: 분 데이터만 사용

## 이유

1. **정확도**: 분 데이터가 가장 정확
2. **단순성**: 하나의 데이터 소스만 유지
3. **일관성**: 동일한 데이터로 개발/테스트/운영

---

**이 정책은 절대적이며 예외 없음**
