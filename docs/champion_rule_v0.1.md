# GARAM DGEFinal 집중 스윙 엔진 (Champion Rule)

**버전**: v0.1 Spec
**목적**: 코스피/코스닥 상위 유동성 종목 100개를 대상으로 부합도(score) 기반 집중 투자 + 오버나잇 스윙을 수행하여 계좌 단위 연 복리 30% 이상을 목표로 함.

## 1. 전략 개요

### 1.1 핵심 컨셉

# GARAM DGEFinal 집중 스윙 엔진 (Champion Rule)

**버전**: v0.1 Spec
**목적**: 코스피/코스닥 상위 유동성 종목 100개를 대상으로 부합도(score) 기반 집중 투자 + 오버나잇 스윙을 수행하여 계좌 단위 연 복리 30% 이상을 목표로 함.

## 1. 전략 개요

### 1.1 핵심 컨셉

1. **Universe & Score**: 100종목에 대해 매일 "DGE 스타일 부합도(score)"를 계산.
2. **Concentration**: Score가 높은 소수 종목에 자본을 집중(몰빵 허용). Score가 낮으면 전액 관망.
3. **Attack Engine**: 개별 종목 매매는 `DGEFinalStrategy` (Intraday ORB + fs_fast + fm)가 담당. 정교한 진입 후 추세가 유지되면 스윙 홀딩.
4. **Compounding**: 레버리지 없이, 매일 원금+수익 전액 재투자(완전 복리).

### 1.2 철학

* **수익 최우선**: 공격력을 최대화. 리스크 관리는 엣지가 약한 구간에서 베팅을 줄이는 것으로 해결.
* **공격 = 안전판**: 별도의 방어 전략 없음.
* **집중 투자**: "애매한 100개 분산보다 확실한 1개 집중이 낫다."
* **Compounding**: 레버리지 없이, **매 포트폴리오 재배분·진입 시점마다 계좌 전체(원금+누적 수익)를 기준으로 포지션을 계산하는 완전 복리 구조.**

## 2. 엔진 구조 (3층 아키텍처)

### 2.1 1층: Universe & Score 엔진

* **대상**: 시총 상위/유동성 높은 100종목.
* **Score**: DGE 스타일(트렌드, 레짐, 변동성) 부합도 [0, 1].
* **도구**: `scripts/analysis/score_universe_for_dgefinal.py` (Skeleton Ready, Logic TBD)

### 2.2 2층: 포트폴리오 배분 엔진 (집중·몰빵)

* **관망 게이트**: `score_max < T_gate` (0.15~0.3) 이면 전액 현금(Exposure 0).
* **집중 배분**:
  * Score 내림차순 정렬.
  * `w_i = min(score_i, Remaining_Capital)` 방식으로 순차 배분.
  * 예: 1등 Score가 1.0이면 100% 몰빵.

### 2.3 3층: 개별 종목 공격 엔진 (DGEFinal)

* **전략**: `DGEFinalStrategy` (Hybrid V1 + M_ATTACK_V3 Wrapper).
* **진입**: Intraday ORB + fs_fast + fm.
  * STRONG_UP 레짐: `fs_orb >= 0.3` (공격적).
  * 기타: `fs_orb >= 0.5`.
* **리스크**:
  * 강한 레짐: Risk ~1.5%.
  * 약한 레짐: Risk ~0.3%.
* **청산/스윙**:
  * 장중 추세 붕괴 시 즉시 손절.
  * 강한 추세 유지 시 오버나잇(Swing) 허용.

## 3. 운용 플로우 (Daily)

1. **장 시작 전**: Score 계산 및 포트폴리오 배분 결정.
2. **장중**: `DGEFinal`이 각 종목별 Intraday 진입/청산/관리 수행.
3. **장 마감**:
    * `should_hold_overnight` 체크 (레짐/추세 유지 시 홀딩).
    * 나머지 청산.
4. **정산**: Trade-by-Trade PnL 반영하여 다음 진입 시 자본(Equity) 갱신 (완전 복리).

## 4. 검증 기준

* **벤치마크 (참고용 최소 기준)**:
  * 집중 스윙 (Score > 0.15, Hold): **+71.55%** (6개월, 과거 실험 기준)
  * 집중 투자 (Score 기반): **+56.22%** (6개월, 과거 실험 기준)
  * *해석: 위 수치는 Champion Rule 설계 이전 실험에서 얻은 보수적 성과로, 본 전략의 **최소 기대 레벨(참고 기준)**로 사용하며, v0.1 이후 백테스트는 완전 복리/최신 룰로 다시 검증한다.*
* **리스크 프로파일**: MDD -50%~-60% 감내 (공격형).

## 5. 구현 체크리스트

* [ ] `score_universe_for_dgefinal.py` (Skeleton 작성됨, 실제 Score 로직 구현 필요)
* [ ] `run_live_dge_final.py`에 포트폴리오 배분 로직(Layer 2) 탑재.
* [ ] `DGEFinalStrategy`에 스마트 오버나잇 로직(Layer 3) 탑재.
* [ ] 완전 복리 자본 관리 시스템 구축 (Trade-by-Trade Equity Update).
