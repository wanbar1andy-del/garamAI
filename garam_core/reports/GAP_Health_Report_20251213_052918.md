# GAP (Garam Audit & Pause) - Health Report

- **Status:** PROJECT FROZEN (P0 STOP)
- **Generated At:** 2025-12-13 05:29:09 UTC
- **Project Root:** `G:\내 드라이브\garam\garam\garam_core`
- **Overall Health:** **FAIL**

## Summary
- PASS: 11
- WARN: 0
- FAIL: 1

## Checks
| Check | Status | Detail |
|---|---:|---|
| Gate0: environment(paths.yaml) | **PASS** | paths.yaml loaded and validated |
| path exists: project_root | **PASS** | G:\내 드라이브\garam\garam\garam_core |
| path exists: data_root | **PASS** | G:\내 드라이브\garam\garam\GARAM_Data |
| path exists: logs_root | **PASS** | G:\내 드라이브\garam\garam\logs |
| artifact: close_matrix.parquet | **FAIL** | not found. searched: G:\내 드라이브\garam\garam\GARAM_Data\history\close_matrix.parquet, G:\내 드라이브\garam\garam\GARAM_Data\close_matrix.parquet, G:\내 드라이브\garam\garam\garamdata\history\close_matrix.parquet |
| artifact: universe_kr_top50.yaml | **PASS** | found: G:\내 드라이브\garam\garam\garam_core\config\universe_kr_top50.yaml |
| data scan: corrupt csv | **PASS** | csv=316, parquet=0 |
| universe parse (best-effort) | **PASS** | loaded 316 symbols (sample=['000080', '000100', '000120', '000150', '000155']) |
| Gate1: schema sample | **PASS** | validated 3 sample symbols |
| smoke replay: 000080/minute | **PASS** | metrics={'total_return': -0.013127161342563531, 'max_drawdown': -0.028456019900248042}, trades=18 |
| smoke replay: 000100/minute | **PASS** | metrics={'total_return': 0.0002392060996854184, 'max_drawdown': -0.04029223731437581}, trades=20 |
| recollect consistency | **PASS** | universe/history aligned (316) |

## Details (FAIL/WARN)
## Action Recommendations (Gate-Driven)
- **P0:** 필수 아티팩트(클로즈 매트릭스/유니버스) 누락. 해당 파일 위치 확정 및 생성/복구 후 재검증.

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
  "exists": true,
  "csv_count": 316,
  "parquet_count": 0,
  "corrupt_csv": [],
  "examples": [
    "005930.csv",
    "000660.csv",
    "373220.csv"
  ]
}
```
