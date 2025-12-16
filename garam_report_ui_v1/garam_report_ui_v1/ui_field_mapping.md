# GaramUI 필드 매핑 (Report v1)

## 데이터 소스
- UI는 `garam_core/reports/latest.json`만 읽는다.
- 과거 조회는 `reports/<run_id>/report.json` 목록에서 선택.

## Overview
- Status badge: `summary.status`
- Headline: `summary.headline`
- KPIs: `summary.kpis.*`

## Checks Table
- Rows: `checks[]`
- Columns:
  - id: `checks[i].id`
  - name: `checks[i].name`
  - status: `checks[i].status`
  - severity: `checks[i].severity`
  - 주요 metric 1~2개: `checks[i].metrics`에서 선택(예: missing_ratio, rejects, latency p95 등)
  - evidence count: len(`evidence_paths`)
  - logs count: len(`log_paths`)

## Check Details
- Header: `{id} — {name}`
- Status/Severity
- Metrics: key-value
- Notes: bullet list
- Evidence/Logs: 클릭 가능한 파일 링크(로컬/드라이브 경로 정책에 맞게)
