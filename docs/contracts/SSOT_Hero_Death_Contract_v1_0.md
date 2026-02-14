# SSOT Hero Death Contract v1.0

- 문서명: SSOT_Hero_Death_Contract_v1_0.md
- 버전: 1.0
- 최종수정: 2025-12-20
- 목적: 히어로(Top-K) 상태에서 “내려오는 때”를 **이벤트(Death)로 박제**하여, 탈출(Exit) 규칙을 빠르게 연구/검증한다.

---

## 0. 핵심 원칙 (봉인)

1) Death는 “감”이 아니라 **라벨 기반 이벤트**다.
2) Death 이벤트는 **앵커 기반(예: 5분)** 으로 판정한다.
3) 탈출 연구는 “더 빨리”가 목표이며, 최소 조건은 **비용 차감 후에도 수익 보호**다.

---

## 1. 입력

- Hero Label Contract v1.0 산출물(필수):
  - `hero_flag`, `rank`, `net_rel_ret`, `ref_price`, `anchor_ts`
- (선택) 보조 피처(연구용):
  - VWAP, EMA, Squeeze, Vol_z, 호가/체결 기반 지표 등

---

## 2. Death 이벤트 타입 정의

### D1. Top-K 이탈 (Rank Exit)

- 조건:
  - 이전 앵커에서 `hero_flag=1` AND 현재 앵커에서 `rank > K` 또는 `hero_flag=0`
- 의미:
  - “히어로 자격 상실” (상대 우위가 꺾임)

### D2. 비용 반영 우위 붕괴 (Net Edge Break)

- 조건:
  - 이전 앵커에서 `net_rel_ret > 0` AND 현재 앵커에서 `net_rel_ret <= 0`
- 의미:
  - “비용까지 감안하면 이 구간은 더 이상 돈이 안 됨”
- 우선순위:
  - **진입/유지의 최소 조건**과 직결 → 매우 중요

### D3. 연속 약화 (Sustained Decay)

- 윈도우 W(예: 6 = 30분)에서 유효 히어로 비율이 임계치 이하
- 조건(예시):
  - 최근 W개 앵커에서 `hero_flag=1` 비율 < `min_live_ratio` (예: 0.33)
- 의미:
  - “회복 없는 약화 → 더 늦기 전에 탈출”

---

## 3. Death 이벤트 산출물 스키마 (Output)

파일: `results/death/hero_death_events_{YYYYMMDD}.csv` (또는 기간 단위)

필수 컬럼:

- `date`
- `symbol`
- `death_ts` : Death 판정 앵커 시각
- `death_type` : D1/D2/D3
- `k` : Top-K 값
- `prev_rank`, `rank`
- `prev_net_rel_ret`, `net_rel_ret`
- `notes` : 보조 사유(해당 시)

권장 컬럼(연구/디버그):

- `drawdown_from_peak` : 히어로 구간 내 최고점 대비 하락률
- `time_in_hero` : 히어로 유지 시간(분)
- `peak_net_rel_ret` : 구간 내 최대 net_rel_ret
- `exit_horizon_test` : Death 후 H분 추가 보유 시 손익(비교용)

---

## 4. 탈출 규칙 연구(가설) 템플릿

Death를 기준으로 “빠른 탈출” 가설을 구조화한다.

예:

- Rule X: D2 발생 시 즉시 EXIT (다음 앵커)
- Rule Y: D1 발생 + Vol_z 급락 동반 시 EXIT
- Rule Z: D3 발생 시 EXIT (추세 종료)

각 룰은 반드시 다음 지표로 평가:

- 비용 차감 후 PnL 개선 여부
- 평균 손실 축소(MDD/손절 회수)
- 승률/기대값 변화

---

## 5. Fail-Fast 품질 게이트

- Death 이벤트가 생성되었는데 참조 라벨이 없으면 KILL
- `death_ts`가 세션 범위를 벗어나면 KILL
- `prev_*` 값이 누락된 상태에서 Death 판정이 되면 KILL (상태관리 오류)

---
(끝)
