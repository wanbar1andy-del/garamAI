# Turbo V3 Verified Result (005940)

## Meta

- Run ID: `verify_turbo_v3_005940_20251215_010342`
- Timestamp (UTC): `2025-12-15T01:03:42Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005940` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2931, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1448923.8217080284

## Key Points

- Total Return: -98.55%
- Max Drawdown: -98.64%
- Trades: 2931
- Final Equity: 1,448,924 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1465

- Win Rate: 29.76%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00020

- **Expectancy (Net)**: **-0.00260**

- Net PnL Total: -3.80683

- SQN Score: -16.63020


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 256 | 2 | 100.00% | **0.01539** |  |
| TREND_DOWN | 167 | 1 | 100.00% | **-0.00066** |  |
| CHOP_HIGHVOL | 1734 | 26 | 30.77% | **-0.00288** |  |
| CHOP_LOWVOL | 92450 | 1408 | 29.47% | **-0.00268** |  |
| PANIC | 1133 | 28 | 35.71% | **0.00030** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00279

- Last 20% Median Exp: -0.00234

- Drop Ratio: 16.05%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
