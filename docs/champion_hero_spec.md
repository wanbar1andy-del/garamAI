# Champion Hero Strategy Specification (SSOT)

Version: 1.0
Date: 2025-12-19
Source: User Directive (Based on Garam251215)

## 1. Philosophy: "2/5/0 Rule based on Signal Strength"

- **Goal**: Identify the best stocks ("Heroes") regarding Momentum/Edge each day.

### B. Position Sizing (2/5/0 Rule)

- **Strong Signal**: 2 Positions (Concentrated).
- **Weak Signal**: 5 Positions (Diversified).
- **No Signal**: 0 Positions (Cash).
*Note: Determined by Champion Score Strength & Spread.*
- **Allocation**: Dynamic exposure based on signal strength (2, 5, or 0 positions).
- **Cycle**: Scan -> Enter -> Hold/Swing -> Cut/Rotate.

### 3. Selection Logic (Champion Score)

**Score = f(ORB_Breakout, fs_fast, fm_daily_trend)**

- **Ranking**: All candidates passing Veto are ranked by Score.
- **Eligibility (Champion Mode)**:
  - `Gate Pass`: Score ≥ `T_WEAK` (0.0)
  - `No Regime Ban`: Index > MA20 OR Vol_Accel < Threshold
  - *Note*: `is_hero` flag (Expectancy) is IGNORED for eligibility in this mode.
- **Eligibility (MR Mode)**:
  - Strict `is_hero` (Expectancy > 0, WinRate > 50%) required.

### 4. Veto Filter (The "B" Brake)

**오직 다음 2가지 조건만 진입을 막는다 (Hard Veto):**

- **Vol_Accel** (ATR_5 / ATR_60) > 1.5
- **ATR%** (ATR_20 / Price) > 10%
*(Note: Expectancy, WinRate 등 과거 통계는 참고용이며 Veto 하지 않음)*

### B. Filtering (Pre-Entry)

- **Overheat Guard**: Exclude if `Vol_Accel` or `ATR_PCT` is already extreme (avoid catching a falling knife or exhausted top).
- **Regime Check**: Must align with Market Regime (R1~R5).
  - *Bull*: Aggressive Entry.
  - *Bear/Crash*: Block Entry (Cash Preservation).

## 2. Operations & Life Cycle

### A. Entry

- **Timing**: End of Day (for Swing) or Breakout Trigger (Next Open).
- **Allocation**: 100% of Risk Capital to the Top 1-2 Candidates.

### B. Holding (Smart Swing)

- **Overnight**: Allowed by default ("Smart Swing").
- **Condition**: Hold as long as the "Hero Status" is maintained.

### C. Exit (The "Death" of a Hero)

- **Immediate Cut**:
  - Volatility Explosion (unexpected direction).
  - Large Loss (breaching Stop Loss).
  - Signal Decay (Rank drop rank < N).
  - **Trigger**: 09:30 이후 "ORB 상단 돌파" + "추세(fm) 상승" 동시 확인.
- **Veto Filter**: `Vol_Accel` > 1.5 또는 `ATR%` > 10% (Expectancy는 Veto 아님, 리포트용).
- **Time Cut**: 16봉(약 4시간) 후 지지부진 시 청산.
- **Fail-Fast**: -5% 손절, -3~4% 경고. Vol_Accel 폭주 시 사망 처리.
- **Rotation**:
  - When current Hero dies or stalls, **immediately** pivot to the "Next Turn's Hero".

### D. Crisis Management

- **Market Crash**: If KOSPI/Market Regime indicates "Fear/Crash":
  - Reduce Exposure to 0% (Cash).
  - Resume only when Fear subsides.

### 5. Allocation Logic (The "2/5/0" Rule)

**Signal Strength Determines 'K' (Exposure)**

- **K=2 (Strong)**:
  - Top1 Score ≥ `T_STRONG` (30bps)
  - **AND** Top2 Score ≥ `T_STRONG`
  - **AND** (Top1/Top2 ≥ `R_STRONG` **OR** Top1-Top2 ≥ `D_STRONG`)
  - **Action**: Top 2 Heroes, 50% each (Target Weight 0.5).
- **K=5 (Weak/Cluster)**:
  - Top1 Score ≥ `T_WEAK` (15bps)
  - Failing Strong Criteria.
  - **Action**: Top 5 Heroes, 20% each (Target Weight 0.2).
- **K=0 (Rest)**:
  - Top1 Score < `T_WEAK`
  - **OR** Regime Ban (Veto).
  - **Action**: **CASH 100%**.

### 6. Parameters (Tunables)

- `T_WEAK`: 0.0015 (15bps)
- `T_STRONG`: 0.0030 (30bps)
- `R_STRONG`: 1.30 (Ratio)
- `D_STRONG`: 0.0010 (Diff)

## 4. Implementation Checklist

### 4.1. Data Structures

- [ ] **HeroProbe**: Define `CHAMPION_STRATEGY` in `scan_heroes.py`.
- [ ] **Calculations**: Add `Vol_Accel`, `ORB_Diff` to `FeatureStore`.

### 4.2. Operational Logic (`HeroDiary`)

- [ ] **Ranker**: Sort by `ChampionScore` (Composite of Momentum + ORB).
- [ ] **Filter**: Apply `OverheatGuard` and `RegimeBan`.
- [ ] **Decision**:
  - `HERO`: Top 1 (Satisfies all gates).
  - `ROTATE`: If Holding != HERO, Sell Holding & Buy HERO.
  - `CASH`: If Regime = Crash.

### 4.3. Execution

- [ ] **Allocation**: Ensure `weight = 1.0` for Hero in `allocation_*.csv`.
- [ ] **Orders**: Verify `build_orders` creates valid BUY orders.

## 5. Success Metric (Fail-Fast)

- **Log**: `HeroDiary` must explain WHY a stock is Hero or Why dropped.
- **Trace**: "Found 1 Hero -> Weight 1.0 -> Buy Order Generated".
