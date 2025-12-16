# GAP (Garam Audit & Pause) - Health Report

- **Status:** PROJECT FROZEN (P0 STOP)
- **Generated At:** 2025-12-13 05:28:23 UTC
- **Project Root:** `G:\내 드라이브\garam\garam\garam_core`
- **Overall Health:** **FAIL**

## Summary
- PASS: 8
- WARN: 1
- FAIL: 3

## Checks
| Check | Status | Detail |
|---|---:|---|
| Gate0: environment(paths.yaml) | **PASS** | paths.yaml loaded and validated |
| path exists: project_root | **PASS** | G:\내 드라이브\garam\garam\garam_core |
| path exists: data_root | **PASS** | G:\내 드라이브\garam\garam\GARAM_Data |
| path exists: logs_root | **PASS** | G:\내 드라이브\garam\garam\logs |
| artifact: close_matrix.parquet | **FAIL** | not found. searched: G:\내 드라이브\garam\garam\GARAM_Data\history\close_matrix.parquet, G:\내 드라이브\garam\garam\GARAM_Data\close_matrix.parquet, G:\내 드라이브\garam\garam\garamdata\history\close_matrix.parquet |
| artifact: universe_kr_top50.yaml | **FAIL** | not found. searched: G:\내 드라이브\garam\garam\garam_core\config\universe_kr_top50.yaml, G:\내 드라이브\garam\garam\garam\garam\config\universe_kr_top50.yaml, G:\내 드라이브\garam\garam\garam\config\universe_kr_top50.yaml |
| data scan: corrupt csv | **PASS** | csv=316, parquet=0 |
| universe parse (best-effort) | **WARN** | universe not parsed; using defaults=['005930', '000660', '035420'] |
| Gate1: schema sample | **PASS** | validated 3 sample symbols |
| smoke replay: 005930/minute | **PASS** | metrics={'total_return': -0.005462103520191164, 'max_drawdown': -0.04822555460692979}, trades=14 |
| smoke replay: 000660/minute | **PASS** | metrics={'total_return': -0.0216652010963585, 'max_drawdown': -0.04011777260695226}, trades=12 |
| recollect consistency | **FAIL** | missing=0, extra=316 |

## Details (FAIL/WARN)
### recollect consistency (FAIL)
```json
{
  "timeframe": "minute",
  "universe_count": 0,
  "history_count": 316,
  "missing_in_history": [],
  "missing_in_history_count": 0,
  "extra_in_history": [
    "000080",
    "000100",
    "000120",
    "000150",
    "000155",
    "000240",
    "000250",
    "000270",
    "000500",
    "000660",
    "000670",
    "000720",
    "000810",
    "000815",
    "000880",
    "000990",
    "0009K0",
    "001040",
    "001120",
    "001430",
    "001440",
    "001450",
    "001570",
    "001720",
    "001800",
    "002380",
    "002790",
    "003090",
    "003230",
    "003380",
    "003490",
    "003540",
    "003550",
    "003570",
    "003670",
    "003690",
    "004000",
    "004020",
    "004170",
    "004370",
    "004800",
    "004990",
    "005070",
    "005290",
    "005300",
    "005380",
    "005385",
    "005387",
    "005440",
    "005490"
  ],
  "extra_in_history_count": 316,
  "history_dir": "G:\\내 드라이브\\garam\\garam\\GARAM_Data\\history\\minute",
  "universe_path": "G:\\내 드라이브\\garam\\garam\\garam_core\\config\\universe_kr_top50.yaml"
}
```

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
