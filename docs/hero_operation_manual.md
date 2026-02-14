# Hero Operation Manual (Phase 6)

**Version**: 1.0
**Date**: 2025-12-19
**Purpose**: Define the **SSOT Rule**, **Hero Diary Schema**, and **Fail-Fast Checklist** for the automated Hero Engine.

---

## 1. SSOT Integrity Rules (The "Iron Laws")

1.  **Universe Unity**: All components (Ingest, Score, Order, Signal) MUST refer to `GARAM_Data/real_universe_400.csv` (SHA-1 tracked).
2.  **Score Existence**: A symbol CANNOT be traded or held if it is missing from the daily Score File.
    *   *Violation*: Immediate **KILL SWITCH**. Matches "Ghost Position" risk.
3.  **Regime Sync**: The `regime` applied to decision logic MUST match the `regime_at_time` in the Score File.

## 2. Hero Diary Schema (`hero_diary_YYYYMMDD.csv`)

This file is the "Black Box Recorder" for every daily decision. It must contain the **Top 20 candidates** + **All Current Holdings**.

| Column | Type | Description | SSOT Source |
|---|---|---|---|
| `date` | str | YYYYMMDD | System Time |
| `symbol` | str | 6-digit Code | Universe |
| `alpha_score` | float | 0.0 ~ 1.0 | Score File |
| `regime` | str | Regime Label (e.g., BULL, BEAR) | Score File |
| `t_gate_pass` | bool | `score >= 0.15` | Logic Fixed |
| `regime_ban` | bool | True if Regime in [BanList] | Logic Config |
| `rank` | int | Daily Score Rank (1=Highest) | Dynamic Calc |
| **`decision`** | str | **HERO** / **HOLD** / **EXIT** / **DROP** | **Final Output** |
| `target_weight` | float | 0.0 ~ 1.0 (Concentration) | Allocation Logic |
| `reason` | str | Explanation (e.g., "Score < Gate", "Vol Break") | Logic Log |
| `fill_status` | str | FILLED / PF / NONE | Order Bus (Post) |

### Decision States
- **HERO**: New Entry or Re-Entry (Top Score + Gate Pass + Regime OK).
- **HOLD**: Good Existing position (Smart Swing: Score >= 0.5 & PnL > 0).
- **EXIT**: Forced liquidation (Vol Break / Score Drop / Regime Ban).
- **DROP**: Candidate failed selection (e.g., Rank 3 but Budget Full).

## 3. Daily Operational Checklist (Fail Fast)

The `run_daily_ops.py` script MUST execute these checks sequentially. Any **[FAIL]** stops the pipeline strictly.

### Pre-Flight (15:35)
1.  **[ ] Data Integrity**: `audit_data_quality_1y.py` (Last 1M) returns OK.
2.  **[ ] Universe Check**: `real_universe_400.csv` row count == 401.
3.  **[ ] Score File Check**: Today's `hero_scores_*.csv` exists.
    *   *Check*: Does it cover all currently held symbols? (Crucial)

### In-Flight (Selection)
4.  **[ ] Gate Logic**: Ensure no symbol with `score < 0.15` is marked **HERO**.
5.  **[ ] Regime check**: If Regime is Defensive, satisfy strictly limited budget.

### Post-Flight (Validation)
6.  **[ ] Order Consistency**: `orders/inbox` count == `Hero Diary` "New/Exit" count.
7.  **[ ] Log Archive**: `hero_diary` saved to `results/diary/`.

---

## 4. Execution Trigger (Intraday)

*   **Selection**: 15:30 (Close Data) -> Score -> Diary -> Allocation.
*   **Execution**: 15:40 (After Market) or Next Open (09:00).
    *   *Operation*: Paper Trading currently uses **Next Open** (Day+1 09:00) logic for execution simulations, or **After Hours** if supporting formatted orders.
    *   *Current Phase*: Focus on **Next Open** (09:00) execution to match `HOLD_1D` logic.

## 5. Next Steps

1.  Implement `HeroDiaryBuilder` class.
2.  Inject `FailFast` checks into `run_daily_ops.py`.
3.  Archive this manual as standard.
