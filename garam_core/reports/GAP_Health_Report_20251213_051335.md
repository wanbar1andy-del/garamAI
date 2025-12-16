# GAP (Garam Audit & Pause) - Health Report

- **Status:** PROJECT FROZEN (P0 STOP)
- **Generated At:** 2025-12-13 05:13:35 UTC
- **Project Root:** `G:\내 드라이브\garam\garam\garam_core`
- **Overall Health:** **FAIL**

## Summary
- PASS: 5
- WARN: 1
- FAIL: 6

## Checks
| Check | Status | Detail |
|---|---:|---|
| Gate0: environment(paths.yaml) | **PASS** | paths.yaml loaded and validated |
| path exists: project_root | **PASS** | G:\내 드라이브\garam\garam\garam_core |
| path exists: data_root | **PASS** | G:\내 드라이브\garam\garam\GARAM_Data |
| path exists: logs_root | **PASS** | G:\내 드라이브\garam\garam\logs |
| artifact: close_matrix.parquet | **FAIL** | not found. searched: G:\내 드라이브\garam\garam\GARAM_Data\history\close_matrix.parquet, G:\내 드라이브\garam\garam\GARAM_Data\close_matrix.parquet, G:\내 드라이브\garam\garam\garamdata\history\close_matrix.parquet |
| artifact: universe_kr_top50.yaml | **FAIL** | not found. searched: G:\내 드라이브\garam\garam\garam_core\config\universe_kr_top50.yaml, G:\내 드라이브\garam\garam\garam\garam\config\universe_kr_top50.yaml, G:\내 드라이브\garam\garam\garam\config\universe_kr_top50.yaml |
| data scan: history/minute | **FAIL** | missing: G:\내 드라이브\garam\garam\GARAM_Data\history\minute |
| universe parse (best-effort) | **WARN** | universe not parsed; using defaults=['005930', '000660', '035420'] |
| Gate1: schema sample | **FAIL** | pass=0, fail=3 |
| smoke replay: 005930/minute | **FAIL** | DataLoadError: History dir not found: G:\내 드라이브\garam\garam\GARAM_Data\history\minute |
| smoke replay: 000660/minute | **FAIL** | DataLoadError: History dir not found: G:\내 드라이브\garam\garam\GARAM_Data\history\minute |
| recollect consistency | **PASS** | universe/history aligned (0) |

## Details (FAIL/WARN)
### Gate1: schema sample (FAIL)
```json
{
  "details": [
    {
      "symbol": "005930",
      "error": "DataLoadError: History dir not found: G:\\내 드라이브\\garam\\garam\\GARAM_Data\\history\\minute"
    },
    {
      "symbol": "000660",
      "error": "DataLoadError: History dir not found: G:\\내 드라이브\\garam\\garam\\GARAM_Data\\history\\minute"
    },
    {
      "symbol": "035420",
      "error": "DataLoadError: History dir not found: G:\\내 드라이브\\garam\\garam\\GARAM_Data\\history\\minute"
    }
  ]
}
```

### smoke replay: 005930/minute (FAIL)
```json
{
  "trace": "Traceback (most recent call last):\n  File \"C:\\garam\\garam\\garam_core\\health\\diagnostic_report.py\", line 188, in _run_smoke_replay\n    res = run_replay(\n        project_root=project_root,\n    ...<5 lines>...\n        collect_debug=False,\n    )\n  File \"C:\\garam\\garam\\garam_core\\replay\\replay_runner.py\", line 97, in run_replay\n    df_raw = load_ohlcv(\n        data_root=paths.data_root,\n    ...<2 lines>...\n        spec=LoadSpec(tz=replay.timezone),\n    )\n  File \"C:\\garam\\garam\\garam_core\\data\\loader.py\", line 55, in load_ohlcv\n    raise DataLoadError(f\"History dir not found: {base_dir}\")\ngaram_core.data.loader.DataLoadError: History dir not found: G:\\내 드라이브\\garam\\garam\\GARAM_Data\\history\\minute\n"
}
```

### smoke replay: 000660/minute (FAIL)
```json
{
  "trace": "Traceback (most recent call last):\n  File \"C:\\garam\\garam\\garam_core\\health\\diagnostic_report.py\", line 188, in _run_smoke_replay\n    res = run_replay(\n        project_root=project_root,\n    ...<5 lines>...\n        collect_debug=False,\n    )\n  File \"C:\\garam\\garam\\garam_core\\replay\\replay_runner.py\", line 97, in run_replay\n    df_raw = load_ohlcv(\n        data_root=paths.data_root,\n    ...<2 lines>...\n        spec=LoadSpec(tz=replay.timezone),\n    )\n  File \"C:\\garam\\garam\\garam_core\\data\\loader.py\", line 55, in load_ohlcv\n    raise DataLoadError(f\"History dir not found: {base_dir}\")\ngaram_core.data.loader.DataLoadError: History dir not found: G:\\내 드라이브\\garam\\garam\\GARAM_Data\\history\\minute\n"
}
```

## Action Recommendations (Gate-Driven)
- **P0:** 필수 아티팩트(클로즈 매트릭스/유니버스) 누락. 해당 파일 위치 확정 및 생성/복구 후 재검증.
- **P0:** 스키마 검증 실패. 컬럼/타임존/정렬 규약을 데이터 저장 단계에서 강제하고, schema gate 통과 전에는 리플레이 금지.
- **P1:** 리플레이 스모크 실패. loader→schema→engine 순으로 실패 지점부터 역추적(Trace)하여 1건이라도 PASS 만들 것.

## Context
```json
{
  "project_root": "G:\\내 드라이브\\garam\\garam\\garam_core",
  "data_root": "G:\\내 드라이브\\garam\\garam\\GARAM_Data",
  "logs_root": "G:\\내 드라이브\\garam\\garam\\logs"
}
```
```json
{
  "base_dir": "G:\\내 드라이브\\garam\\garam\\GARAM_Data\\history\\minute",
  "exists": false,
  "csv_count": 0,
  "parquet_count": 0,
  "corrupt_csv": [],
  "examples": []
}
```
