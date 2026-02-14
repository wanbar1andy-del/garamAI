# SSOT Sealing Checklist v1.1 (AUDIT-SEALED)

**Status**: **AUDIT-SEALED** (Ready for Long-Term Maintenance)
**Target Engine**: `scripts/replay_1month_test.py`
**Verified Result**: `HOLD_1D` = **+19.23%** (Period: 2025-11-18 ~ 12-17)

## 0. SSOT Contract (Definitive)

| Dimension | Definition |
|---|---|
| **Scope** | `scripts/replay_1month_test.py` (Probe=`MR_RSI_30`, Exit=`HOLD_1D`, Cost=`30bps`) |
| **Cost Semantics** | `roundtrip_total_bps` (Applied as `cost_bps/2` on Entry and `cost_bps/2` on Exit) |
| **Data Constraint** | **Kiwoom 1Y Rolling** logic via `load_minute_robust.py` (sorting fixed) |
| **Fill: EOD** | `MINUTE_BAR.eod_close` (Last bar of `dt.date == trade_date.date()`) |
| **Fill: Next Open** | Priority: `09:00 Open` > `First Bar Open` > `First Bar Close (Proxy)` |

## 1. Applied Patches (Robustness)

These patches are permanently merged to guarantee the contract above.

| Component | Patch Description | Status |
|---|---|---|
| **Date Slicing** | `_get_day_slice`: Uses `df['dt'].dt.date == date.date()` to guarantee daily isolation. | ✅ Applied |
| **EOD Safety** | `_get_eod_close_fill`: Explicit fallback. returns `MINUTE_BAR.eod_close`. | ✅ Applied |
| **Open Logic** | `_get_next_open_fill`: Strict priority logic. Validates `09:00` existence. | ✅ Applied |
| **Crash Guard** | `process_exits`: Handles `price is None` gracefully without crashing. | ✅ Applied |

**Manifest Additions**:

- `open_fill_policy`: "0900_bar_open > first_bar_open > first_bar_close_proxy"
- `eod_fill_policy`: "minute_day_last_close"

## 2. Reproducibility Proof

### 2.1 Must-Match Invariants

Any "re-run" claiming to be SSOT must match these values exactly.

- **`return_pct`**: **+19.23%** (Tolerance: ±0.05%p for OS math diffs)
- **`total_trades`**: **253**
- **`n_equity_points`**: **22** (Daily)
- **`cost_semantics`**: `roundtrip_total_bps`
- **`open_proxy_rate`**: **0.0%** (for `NEXT_OPEN` runs) or N/A (for `HOLD_1D`)

### 2.2 Tolerance Rule

- **Strict**: Logic bugs (e.g. trading on holidays) are Zero Tolerance.
- **Loose**: Floating point LSB differences (python versioning) allowed up to `0.05%p`.

### 2.3 Artifact Pairing

Every valid run MUST produce:

1. `manifest.json` (Configuration & Fill Policy)
2. `metrics_verified.json` (Calculated Stats)
3. `equity_curve.csv` (Time Series)
4. `all_trades.csv` (Audit Trail)

## 3. Maintenance Rules (Do Not Touch)

1. **Immutable Calendar**: Do not modify `get_trading_days`. It must scan actual data.
2. **Immutable Fill**: Do not modify `_get_next_open_fill` logic.
3. **Benchmark Guardrail**:
    - ALWAYS run `scripts/calc_benchmarks.py` with every test.
    - **Red Flag**: If `Engine Return` < `Universe EW Return`, the engine is failing to capture Beta.
    - **Bull Market Rule**: If `Engine` < `Single Anchor (Samsung)`, investigate "Friction/Timing" immediately.

## 4. Verification Command

### Step 1: Execute Replay

```powershell
python -m scripts.replay_1month_test --start 20251118 --end 20251217 --universe GARAM_Data/real_universe_400.csv --minute_dir GARAM_Data/history/minute --exit HOLD_1D --cost_bps 30
```

### Step 2: Verify Metrics

```powershell
python -m scripts.verify_replay_metrics --equity results/replay/<RUN_ID>/equity_curve.csv --out results/replay/<RUN_ID>/metrics_verified.json
```

**Pass Condition**: `return_pct` ≈ 19.23%, `total_trades` == 253.
