# GARAM Report v1 스키마 (SSOT=JSON)

## 목적
- **Single Source of Truth(SSOT)**: `report.json`
- **표현물(사람용)**: `report.md` (JSON으로부터 생성)
- UI(GaramUI)는 **JSON만 파싱**한다.

## 파일 레이아웃
```
garam_core/
  reports/
    latest.json
    latest.md
    <run_id>/
      report.json
      report.md
      logs/
      evidence/
      plots/
```

## report.json (필수 필드)
### meta (필수)
- `run_id` (string): 예) `2025-12-15T10-22-31Z__RUN123`
- `timestamp_utc` (string, ISO8601)
- `mode` (string): `backtest | replay | live`
- `env` (object): `{ "os": "...", "python": "...", "hostname": "...", "user": "..." }`
- `git` (object): `{ "commit": "...", "branch": "...", "dirty": true/false }`
- `data` (object): `{ "universe": "...", "timeframe": "minute|daily|tick", "from": "...", "to": "..." }`

### summary (필수)
- `status` (string): `PASS | WARN | FAIL`
- `headline` (string): 1줄 요약
- `key_points` (array[string]): 3~7개
- `kpis` (object): UI에 바로 노출할 핵심 지표
  - 예) `{ "trades": 123, "win_rate": 0.56, "pnl": 1234567, "mdd": -0.12, "slippage_bps_est": 8.5 }`

### checks (필수)
- 배열. 각 체크는 아래 필드 포함:
  - `id` (string): 예) `DATA_INTEGRITY`
  - `name` (string): 예) `Data Integrity`
  - `status` (string): `PASS | WARN | FAIL | SKIP`
  - `severity` (string): `LOW | MED | HIGH | CRIT`
  - `metrics` (object): 체크별 정량 지표
  - `notes` (array[string]): 체크별 코멘트 (짧게)
  - `evidence_paths` (array[string]): 관련 파일 경로 (reports/<run_id>/evidence/..)
  - `log_paths` (array[string]): 관련 로그 경로
  - `tags` (array[string]): 검색/필터링용 태그

### artifacts (필수)
- `paths` (object):
  - `report_md` (string)
  - `report_html` (string, optional)
- `plots` (array[object], optional):
  - `{ "title": "...", "path": "...", "kind": "equity_curve|dd|heatmap|..." }`

### links (선택)
- `external` (array[object]): 외부 링크가 필요하면
  - `{ "title": "...", "url": "..." }`

## 상태 결정 규칙(권장)
- FAIL: 실거래 중단/배포 금지/킬스위치
- WARN: 자동 디레버리지/거래 축소/관찰 모드
- PASS: 정상 진행
