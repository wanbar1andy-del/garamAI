# SSOT Hero Label Contract v1.1

- 문서명: SSOT_Hero_Label_Contract_v1_0.md
- 버전: 1.1 (Revised)
- 최종수정: 2025-12-20
- 목적: **분봉(1m) 기반 히어로(주도 구간) 라벨을 SSOT로 고정**하여, 이후 Score/룰/탈출(Death) 연구가 “정답 데이터”를 기준으로 진행되게 한다.
- 변경점: 외부 지수(KOSPI) 의존성 제거 → **Universe Index(EW/Median) 내부 생성** 강제.

---

## 0. 핵심 원칙 (봉인)

1) **분봉 그대로** 사용한다.
2) 히어로는 “예측”이 아니라 **사후 수익으로 정의되는 정답 라벨**이다.
   - **"같은 시간대에서 가장 높고 오래 가는 종목 1개"**
3) 진입의 최소조건은 **비용 차감 후 순수익(Net > 0)** 이다.
4) **Universe Index**를 기준선(Baseline)으로 사용하여 상대우위를 측정한다.

---

## 1. 입력 데이터 (Input)

### 1.1 종목 분봉 (필수)

- 소스: `GARAM_Data/history/minute/{symbol}.csv` (400종목 전체)
- 컬럼: `date, open, high, low, close, volume`

### 1.2 Universe Index (Generated SSOT)

- 외부 지수 파일 의존성을 제거하고, 400종목의 통계로 기준선을 만든다.
- 정의: 분봉 시점별 `Median(Close Change)` 또는 `Equal-Weight Index`.
- 목적: 개별 종목의 움직임이 **"시장 전체 분위기 대비 얼마나 강한가"**를 측정하기 위함.

---

## 2. 라벨 및 구간 정의 (Label & Segment)

### 2.1 앵커(Anchor) 및 수익률

- 앵커: 세션 내 5분 단위 (09:05 ~ 15:15)
- Horizon(H): 15분, 30분, 60분 (기본 30분 권장)
- 상대수익률(Rel Ret): `Symbol_Fwd_Ret - Universe_Fwd_Ret`
- **순상대수익률(Net Rel Ret)**: `Rel_Ret - Cost(10bps)`

### 2.2 히어로 세그먼트 (Hero Segment)

- 단순 점 단위 Top-K가 아니라, **연속된 구간(Segment)**으로 히어로를 정의한다.
- 정의:
  - **Start**: Top-K(예: 5) 진입 시점
  - **End**: Top-K 이탈 시점 또는 Net Rel Ret < 0 전환 시점
  - **Segment Score**: `Sum(Net Rel Ret * Duration)` (면적)

---

## 3. 라벨 산출물 스키마 (Output)

### 3.1 Hero Segments (핵심 정답지)

- 파일: `results/labels/day={YYYYMMDD}/hero_segments.csv`
- 컬럼:
  - `symbol`
  - `start_time`, `end_time`
  - `duration_min` (지속시간)
  - `avg_rank` (구간 내 평균 순위)
  - `total_net_rel_ret` (누적 순상대수익)
  - `segment_score` (면적 점수)
  - `max_rel_ret` (최대 폭발력)

### 3.2 Hero Rank (일간 요약)

- 파일: `results/labels/day={YYYYMMDD}/hero_rank.csv`
- 내용: 당일 발생한 세그먼트들을 `segment_score` 내림차순 정렬.
- 용도: "오늘의 1등 히어로" 선정 및 GUI 탐색 리스트.

### 3.3 Visualization Data (GUI용)

- 종목별 오버레이 데이터(JSON/CSV) 생성하여 GUI가 `Universe Index` vs `Symbol`을 즉시 그리도록 지원.
- 400개를 겹쳐 그리는 대신, **Top-20 후보 목록**을 클릭하면 해당 종목과 유니버스 지수만 비교하여 그린다.

---

## 4. 품질 게이트 (Fail-Fast)

- (G1) Universe Index 생성 불가(데이터 부족) 시 중단.
- (G2) 당일 히어로 세그먼트가 하나도 없을 경우(변동성 실종), 빈 파일 생성 후 정상 종료(No Trade Proof).

---
