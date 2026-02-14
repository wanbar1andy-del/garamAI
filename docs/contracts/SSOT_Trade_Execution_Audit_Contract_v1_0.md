# SSOT Trade Execution Audit Contract v1.0

- 문서명: SSOT_Trade_Execution_Audit_Contract_v1_0.md
- 버전: 1.0
- 최종수정: 2025-12-20
- 목적: Week-1 등 시뮬레이션 결과의 수익이 정당한지(비용/체결/미래정보 없음)를 **회계적/기계적**으로 규명한다.

---

## 1. 3대 필수 통제 게이트 (Gates)

### Gate A: 체결 모델 (Execution Model)

- **원칙**: 미래정보(Lookahead) 원천 차단.
- **규정**:
  - 신호 발생 시점: $t$ (분봉 close)
  - 체결 시점: $t+1$ (다음 분봉)
  - 체결 가격: $Close[t+1]$ (보수적) 또는 $Open[t+1]$
  - **금지**: $Close[t]$로 즉시 체결 (현실적으로 불가능)

### Gate B: 비용 모델 (Cost Model)

- **원칙**: 비용 없는 수익은 허상이다.
- **규정**:
  - **기본 비용**: 10bps (0.10%) - 수수료/세금/슬리피지 포함
  - **검증 절차(Toggle Test)**:
    1. Cost=10bps 실행: `Net PnL`
    2. Cost=0bps 실행: `Gross PnL`
    - 만약 $|Net - Gross|$가 미미하면 **비용 누락**으로 간주하고 폐기.

### Gate C: 포지션 제약 (Exposure)

- **원칙**: 1x 자본에는 1x 포지션만 존재.
- **규정**:
  - **단일 포지션 원칙**: 동시에 1종목만 보유 (100% 비중).
  - **갈아타기(Switching)**: 기존 포지션 전량 매도 후, 신규 포지션 전량 매수. (Transaction이 2건 발생해야 함)
  - **현금 비중**: 포지션 없을 때는 100% 현금 보유. 재투자는 `Equity` 기준.

---

## 2. 갈아타기 및 탈출 정책 (Policy)

### Switch Policy v0 (검증용 표준)

1. **진입**: 현재 시각 Top-1이 **연속 N분(예: 3분)** 유지 시 진입.
2. **유지**: 보유 종목이 Top-K(예: 3위) 이내면 유지.
3. **교체**: 보유 종목이 Top-K 밖으로 **M분(예: 2분)** 이탈 AND 신규 Top-1 등장 시 교체.
4. **쿨다운**: 교체 후 C분(예: 5분)간 추가 교체 금지 (Whipsaw 방지).

### Death KPI (빠른 도망 지표)

- `reaction_time` = `hero_segment_end_time` - `actual_exit_time`
  - 양수(+): 라벨 종료보다 빨리 나감 (우수)
  - 0: 정시 탈출
  - 음수(-): 늦게 나감 (손실 확대 위험)
- `protected_pnl` = `PnL_if_exit_at_end` - `PnL_actual`

---

## 3. 필수 산출물 (Output Artifacts)

### 3.1 거래 원장 (`trades_week1.csv`)

- 모든 매수/매도/교체 건에 대한 raw ledger.
- 컬럼: `date, time, symbol, side, qty, price, fee, tax, slippage, gross_pnl, net_pnl, balance, reason`

### 3.2 PnL 정합성 리포트 (`pnl_reconciliation_week1.json`)

- 회계적 검증 결과.
- 항목:
  - `equity_start`: 10,000,000
  - `equity_end_calculated`: 잔고 기준 최종 자산
  - `sum_net_pnl`: `sum(trades.net_pnl)`
  - `fee_total`, `tax_total`, `turnover_ratio`
  - **Pass/Fail**: `equity_end ~ (equity_start + sum_net_pnl)` 오차가 10원 미만이어야 함.

### 3.3 Death 감사 리포트 (`death_audit_week1.csv`)

- 탈출 퀄리티 분석.
- 컬럼: `symbol, bucket_time, exit_time, segment_end_time, reaction_time, protected_pnl`

### 3.4 기회비용 리포트 (`opportunity_regret_week1.csv`)

- 매 분(minute)마다 1등을 놓친 기회비용.
- 컬럼: `time, top1_symbol, holding_symbol, top1_ret, holding_ret, regret`

---
(끝)
