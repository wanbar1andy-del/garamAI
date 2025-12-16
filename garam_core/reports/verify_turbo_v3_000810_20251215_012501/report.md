# Turbo V3 Verified Result (000810)

## Meta

- Run ID: `verify_turbo_v3_000810_20251215_012501`
- Timestamp (UTC): `2025-12-15T01:25:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000810` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2984, win_rate=0.00%, pnl=None, mdd=0.00%, equity=782062.5591520811

## Key Points

- Total Return: -99.22%
- Max Drawdown: -99.24%
- Trades: 2984
- Final Equity: 782,063 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1492

- Win Rate: 25.47%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00011

- **Expectancy (Net)**: **-0.00291**

- Net PnL Total: -4.34799

- SQN Score: -18.38221


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 169 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 33 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 411 | 3 | 0.00% | **-0.00568** |  |
| CHOP_LOWVOL | 93809 | 1454 | 25.52% | **-0.00285** |  |
| PANIC | 1257 | 35 | 25.71% | **-0.00515** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00290

- Last 20% Median Exp: -0.00291

- Drop Ratio: -0.37%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
