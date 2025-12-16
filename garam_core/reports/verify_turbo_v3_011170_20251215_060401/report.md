# Turbo V3 Verified Result (011170)

## Meta

- Run ID: `verify_turbo_v3_011170_20251215_060401`
- Timestamp (UTC): `2025-12-15T06:04:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `011170` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2863, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1449097.6295153955

## Key Points

- Total Return: -98.55%
- Max Drawdown: -98.56%
- Trades: 2863
- Final Equity: 1,449,098 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1431

- Win Rate: 27.67%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00017

- **Expectancy (Net)**: **-0.00263**

- Net PnL Total: -3.76002

- SQN Score: -10.73405


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 152 | 1 | 100.00% | **0.00501** |  |
| TREND_DOWN | 78 | 1 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 4658 | 41 | 39.02% | **0.00065** |  |
| CHOP_LOWVOL | 89730 | 1372 | 27.11% | **-0.00270** |  |
| PANIC | 1081 | 16 | 43.75% | **-0.00541** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00279

- Last 20% Median Exp: -0.00249

- Drop Ratio: 10.91%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
