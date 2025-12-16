# Turbo V3 Verified Result (207940)

## Meta

- Run ID: `verify_turbo_v3_207940_20251215_011306`
- Timestamp (UTC): `2025-12-15T01:13:06Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `207940` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2669, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1776452.6755766515

## Key Points

- Total Return: -98.22%
- Max Drawdown: -98.25%
- Trades: 2669
- Final Equity: 1,776,453 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1334

- Win Rate: 28.34%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00013

- **Expectancy (Net)**: **-0.00267**

- Net PnL Total: -3.56683

- SQN Score: -19.11855


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 269 | 1 | 100.00% | **0.02125** |  |
| TREND_DOWN | 147 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 349 | 1 | 100.00% | **0.05609** |  |
| CHOP_LOWVOL | 87398 | 1302 | 28.11% | **-0.00270** |  |
| PANIC | 1097 | 30 | 33.33% | **-0.00411** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00267

- Last 20% Median Exp: -0.00307

- Drop Ratio: -15.12%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
