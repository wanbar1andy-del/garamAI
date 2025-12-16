# Turbo V3 Verified Result (012510)

## Meta

- Run ID: `verify_turbo_v3_012510_20251215_073426`
- Timestamp (UTC): `2025-12-15T07:34:26Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `012510` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2842, win_rate=0.00%, pnl=None, mdd=0.00%, equity=912129.207532192

## Key Points

- Total Return: -99.09%
- Max Drawdown: -99.10%
- Trades: 2842
- Final Equity: 912,129 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1421

- Win Rate: 28.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00019

- **Expectancy (Net)**: **-0.00299**

- Net PnL Total: -4.25416

- SQN Score: -12.80567


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 4 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 53 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 8238 | 90 | 34.44% | **-0.00461** |  |
| CHOP_LOWVOL | 86343 | 1303 | 28.01% | **-0.00285** |  |
| PANIC | 1168 | 28 | 32.14% | **-0.00447** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00283

- Last 20% Median Exp: -0.00315

- Drop Ratio: -11.63%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
