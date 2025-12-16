# Kiwoom 데이터 수집 자동화 가이드

## 개요

이 문서는 Kiwoom API를 통한 한국 주식 시장 데이터의 자동 수집을 설정하는 방법을 설명합니다.

## 무한 루프 방지 기능

모든 스케줄러 스크립트에는 다음 안전 장치가 내장되어 있습니다:

- ✅ **최대 반복 횟수 제한**: `--max-iterations` 옵션
- ✅ **최대 실행 시간 제한**: `--max-runtime-hours` 옵션  
- ✅ **Ctrl+C 안전 종료**: SIGINT 시그널 핸들링
- ✅ **상태 로깅**: 주기적인 진행 상황 로그

## 방법 1: Windows Task Scheduler (권장)

### 설정 단계

1. **Task Scheduler 열기**

   ```
   Win + R → taskschd.msc
   ```

2. **새 작업 만들기**
   - `Create Basic Task` 선택
   - 이름: `GARAM Kiwoom Data Collection`
   - 설명: `매일 15:35에 Kiwoom API 데이터 수집`

3. **트리거 설정**
   - Trigger: `Daily`
   - Start time: `15:35`
   - Recur every: `1 days`

4. **액션 설정**
   - Action: `Start a program`
   - Program/script: `powershell.exe`
   - Add arguments:

     ```
     -ExecutionPolicy Bypass -File "c:\garam\garam\scripts\start_kr_data_collection.ps1"
     ```

5. **조건 설정** (선택사항)
   - Start only if computer is on AC power: ✅
   - Wake the computer to run this task: ✅ (중요!)

6. **설정 확인**
   - Allow task to be run on demand: ✅
   - Run task as soon as possible after a scheduled start is missed: ✅

### 수동 테스트

Task Scheduler에서 작업을 마우스 오른쪽 클릭 → `Run` 선택

## 방법 2: 수동 실행

### 프로덕션 실행

내일 아침 09:00 이전에 실행:

```powershell
cd c:\garam\garam\scripts
.\start_kr_data_collection.ps1
```

스케줄러가 15:35까지 대기한 후 데이터 수집을 실행합니다.

### 시간 제한 실행

4시간 동안만 실행:

```powershell
.\start_kr_data_collection.ps1 -MaxHours 4
```

### 즉시 실행 (테스트용)

스케줄 대기 없이 즉시 한 번 실행:

```powershell
python schedule_kr_data_collection.py --run-now
```

## 방법 3: 테스트 모드

### 단기 테스트

10회 반복 후 자동 종료:

```powershell
.\start_kr_data_collection.ps1 -TestMode
```

### Python에서 직접 테스트

```bash
# 10회 반복
python scripts/schedule_kr_data_collection.py --max-iterations 10

# 1시간 실행
python scripts/schedule_kr_data_collection.py --max-runtime-hours 1

# 즉시 한 번 실행
python scripts/schedule_kr_data_collection.py --run-now
```

## 로그 확인

### 로그 위치

```
g:\내 드라이브\garamdata\logs\scheduler.log
```

### 실시간 로그 모니터링

```powershell
Get-Content "g:\내 드라이브\garamdata\logs\scheduler.log" -Wait -Tail 20
```

## 데이터 저장 위치

수집된 데이터는 다음 경로에 저장됩니다:

```
g:\내 드라이브\garamdata\history\intraday\{symbol}\{interval}\{yyyymmdd}.parquet
```

예시:

```
g:\내 드라이브\garamdata\history\intraday\069500\15m\20251126.parquet
```

## 문제 해결

### 스케줄러가 시작되지 않음

1. Python 경로 확인:

   ```powershell
   python --version
   ```

2. 프로젝트 경로 확인:

   ```powershell
   cd c:\garam\garam\scripts
   Test-Path .\schedule_kr_data_collection.py
   ```

### Kiwoom API 연결 실패

1. Kiwoom OpenAPI+ 설치 확인
2. 32-bit Python 환경 확인
3. 로그인 상태 확인:

   ```powershell
   python scripts/check_kiwoom_session.py
   ```

### 데이터가 저장되지 않음

1. 디렉토리 권한 확인
2. 디스크 공간 확인
3. 로그에서 오류 메시지 확인

## 안전한 종료

실행 중인 스케줄러를 안전하게 종료하려면:

1. **Ctrl+C** 누르기 (PowerShell 창에서)
2. 현재 반복이 완료될 때까지 대기
3. 종료 로그 확인

종료 로그 예시:

```
2025-11-26 18:00:00 - INFO - KRDataCollectionScheduler received SIGINT, will stop after current iteration
2025-11-26 18:00:01 - INFO - KRDataCollectionScheduler stopping: SIGINT
2025-11-26 18:00:01 - INFO - Scheduler stopped: {'name': 'KRDataCollectionScheduler', ...}
```

## 다음 단계

데이터 수집이 정상적으로 작동하면:

1. `scripts/analyze_data_coverage.py`로 데이터 커버리지 확인
2. `scripts/run_dge_daily.py`로 DGE 백테스트 실행
3. GaramUI 대시보드에서 데이터 시각화 확인

## 관련 파일

- 스케줄러 스크립트: `scripts/schedule_kr_data_collection.py`
- 실행 스크립트: `scripts/start_kr_data_collection.ps1`
- 데이터 수집 로직: `scripts/collect_kr_intraday_kiwoom.py`
- 안전 장치 유틸리티: `utils/safe_scheduler.py`
