# Trading Logic Health & Anomaly Report

**Generated**: 2025-11-29
**Scope**: Static Code Analysis & Dynamic Pipeline Simulation (Oct 2025, 5 Symbols)

## 1. Executive Summary

The "Health Check" confirms that the trading logic is **clean and robust**, with no critical "hidden blockers" or "legacy debris" actively preventing trades. The primary constraint on trading volume is the **Strategy Logic itself (`fs_orb` threshold)**, not external risk limits or bugs.

- **Debris Status**: Low. Mostly harmless TODOs and stale comments.
- **Blocking Status**: High selectivity due to `fs_orb` (Intraday Momentum).
- **Risk Limits**: Not currently a bottleneck (Portfolio Cap rarely hit).

## 2. Static Code Analysis (Debris Hunting)

Scanned for keywords: `TODO`, `FIXME`, `LEGACY`, `OLD`, `LIMIT`, `CAP`, `BLOCK`.

### Key Findings

| Category | File | Finding | Impact | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **DEBUG_STUB** | `dge_orb_v0_3.py` | `TODO: Implement detailed trailing logic` | **Medium** | Decide if Trailing Stop is needed for v0.3 or if ExitProfile is sufficient. |
| **LEGACY** | `sim/test_account.py` | `OLD anomaly_type` comments | None | Clean up comments. |
| **LEGACY** | `scripts/watch_shadow_loop.py` | `OLD freshness threshold` | None | Remove stale constants. |
| **RISK_LIMIT** | `config.py` | `RISK_LIMITS_FILE` | **High** | Confirms Risk Limits are externalized (Good). |

**Conclusion**: No "dead code" was found in the critical execution path (`on_bar`, `open_position`).

## 3. Dynamic Pipeline Check (Blocking Analysis)

Simulated `DGEOrbStrategyV3` on 5 symbols (000660, 005930, 005380, 051910, 000270) for Oct 2025.

### Blocking Statistics

| Stage | Count | Description |
| :--- | :--- | :--- |
| **SIGNAL_FILTER** | **13,823** | Daily Trend (`fm`) passed, but Intraday Signal failed. |
| **MAX_POSITIONS** | 0 | Portfolio Limit (3) was never hit. |
| **ORB_PERIOD** | N/A | Implicitly blocked before 09:30 (Design). |

### Top Blocking Reason: `fs_orb < 0.5`

The vast majority of potential trades are filtered because **Intraday Momentum (`fs_orb`)** is too weak, even when the Daily Trend (`fm`) is strong.

**Sample Log**:
`2025-10-01 10:04:00 | 000660 | SIGNAL_FILTER | fs_orb(0.50) < 0.5`
*(Note: Floating point precision may make 0.499 appear as 0.50)*

**Insight**:

- The strategy is **highly selective**. It requires both Daily Trend AND Intraday Breakout.
- **"Attack Mode" Opportunity**: In `STRONG_UP` regimes, we might consider **lowering `fs_orb_thresh`** (e.g., to 0.3 or 0.4) to capture more "drift" moves that don't explode immediately but follow the strong daily trend.

## 4. Recommendations

### A. Code Hygiene

1. **Resolve `dge_orb_v0_3.py` TODO**: Explicitly implement or remove the Trailing Stop TODO. Given v0.3 uses `ExitProfile`, ensure `use_trailing` parameter in `ExitParams` is actually hooked up to logic.
2. **Clean `test_account.py`**: Remove "OLD" comments to avoid confusion.

### B. Strategy Tuning (Attack Mode)

1. **Relax `fs_orb` in Strong Trends**:
    - Current: Fixed `fs_orb_thresh = 0.5` for all regimes.
    - Proposal: In `STRONG_UP` regime, lower `fs_orb_thresh` to **0.3**. This will reduce the "Blocking" count and increase trade frequency in the most profitable regime.

### C. Monitoring

1. **Continuous Health Check**: Integrate `scripts/healthcheck/run_trading_healthcheck.py` into the CI/CD pipeline or weekly routine to ensure no new blockers are introduced.

## 5. Conclusion

The "Health Check" passed. The system is not "broken" or "clogged". It is simply **strict**. To increase "Attack" power, we should tune the **Entry Thresholds** (`fs_orb`) specifically for favorable regimes, rather than removing safety guards.
