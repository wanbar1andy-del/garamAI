# 프로젝트 인벤토리 및 아키텍처 매핑 (AS-IS 분석)

## 1. 개요

현재 프로젝트(`c:\garam\garam`) 내 파일들을 파악하고, 신규 6단계 파이프라인 아키텍처 관점에서 분류함.

## 2. 파일 분류 및 역할 매핑

### [Step 1: INGEST - 수집]

**목표**: 원천 데이터 수집 및 Raw 저장

- `scripts/kiwoom_login_ui.py`: (핵심) 현재 메인 수집기. GUI 기반, 자동 재접속, 증분 수집.
- `collect_incremental.py`: (Legacy) 구버전 증분 수집기. -> `kiwoom_login_ui.py`로 통합됨.
- `collect_kiwoom_400_v2.py`: (Legacy) 구버전 수집기.
- `auto_collect_kiwoom.py`: (Legacy) 자동 수집기.

### [Step 2: VALIDATE - 검증]

**목표**: 데이터 무결성 체크

- `scripts/check_data_integrity.py`: (핵심) 수집된 CSV 파일의 컬럼, 날짜, 사이즈 검사 및 손상 파일 식별.
- `validate_garam.py`: (기타) 이전 검증 스크립트로 추정.

### [Step 3: STORE - 저장]

**목표**: 데이터 저장소 및 설정 관리

- `GARAM_Data/real_universe_400.csv`: (핵심) 수집 대상 종목 리스트 (Universe).
- `garamdata/history/minute/*.csv`: (데이터) 실제 수집된 1분봉 데이터.
- `config.py`: 전역 설정 파일.

### [Step 4: FEATURE - 지표]

**목표**: 기술적 지표 및 팩터 계산

- `features/factory.py`: 지표 생성 팩토리.
- `features/stream_processor.py`: 스트림 데이터 처리.
- `features/pipeline.py`: 피쳐 파이프라인.

### [Step 5: SIGNAL & EXECUTION - 전략/실행]

**목표**: 시그널 생성 및 매매

- `run_minute_complete_backtest.py`: (핵심) 1분봉 데이터 기반 시뮬레이션 및 백테스트.
- `scripts/run_live_trading.py`: 라이브 트레이딩 엔진.
- `broker/kiwoom_connection_manager.py`: 키움 연결 관리자 (실행단).
- `broker/paper_broker.py`: 모의투자 브로커.
- `live/shadow_trader.py`: 쉐도우 트레이딩 모듈.

### [Step 6: MONITOR - 모니터링]

**목표**: 로그, 알림, 리포팅

- `utils/telegram_bot_v2.py`: 텔레그램 알림 봇.
- `utils/event_logger.py`: 이벤트 로거.
- `utils/health_check.py`: 시스템 헬스 체크.
- `logs/`: 시스템 로그 및 백테스트 결과 저장소.

### [Unclassified / Legacy / Test]

**설명**: 리팩토링 대상이거나 삭제 검토 필요

- `test_filesystem.py`, `test_integration.py`: 테스트 스크립트.
- `portfolio_state_*.json`: 시뮬레이션 상태 파일들 (정리 필요).
- `GARAM_AI_ReplayPack_v0_1/*`: 구버전 AI 패키지 잔재.
- `analyze_sep_dd.py`: 개별 분석 스크립트.

---

## 3. 리팩토링 우선순위

1. **정리(Clean-up)**: `collect_*.py` 등 중복된 수집 스크립트를 `/archive`로 이동.
2. **구조화(Structure)**: `/pipeline` 폴더를 생성하고 `01_ingest`, `02_validate` 등의 하위 폴더로 핵심 스크립트 정리/이동.
3. **표준화(Standardize)**: 각 스크립트가 공통 설정(`config.py` 또는 `docs/pipeline_architecture_v2.md`의 스펙)을 따르도록 수정.
