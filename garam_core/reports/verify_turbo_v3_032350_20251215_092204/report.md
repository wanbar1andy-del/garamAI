# Turbo V3 Verified Result (032350)

## Meta

- Run ID: `verify_turbo_v3_032350_20251215_092204`
- Timestamp (UTC): `2025-12-15T09:22:04Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `032350` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2727, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1863320.854204742

## Key Points

- Total Return: -98.14%
- Max Drawdown: -98.15%
- Trades: 2727
- Final Equity: 1,863,321 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1363

- Win Rate: 29.27%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00021

- **Expectancy (Net)**: **-0.00259**

- Net PnL Total: -3.52460

- SQN Score: -11.94883


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 247 | 3 | 33.33% | **-0.01173** |  |
| TREND_DOWN | 36 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3994 | 38 | 28.95% | **0.00002** |  |
| CHOP_LOWVOL | 88633 | 1284 | 28.82% | **-0.00264** |  |
| PANIC | 1551 | 38 | 44.74% | **-0.00257** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00274

- Last 20% Median Exp: -0.00237

- Drop Ratio: 13.77%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
