# Turbo V3 Verified Result (014680)

## Meta

- Run ID: `verify_turbo_v3_014680_20251215_065132`
- Timestamp (UTC): `2025-12-15T06:51:32Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `014680` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2676, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2161054.0565017834

## Key Points

- Total Return: -97.84%
- Max Drawdown: -97.86%
- Trades: 2676
- Final Equity: 2,161,054 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1338

- Win Rate: 32.66%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00023

- **Expectancy (Net)**: **-0.00257**

- Net PnL Total: -3.43266

- SQN Score: -10.28684


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 216 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 186 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6088 | 79 | 26.58% | **-0.00306** |  |
| CHOP_LOWVOL | 87681 | 1225 | 32.73% | **-0.00258** |  |
| PANIC | 1415 | 34 | 44.12% | **-0.00080** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00225

- Last 20% Median Exp: -0.00299

- Drop Ratio: -32.77%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
