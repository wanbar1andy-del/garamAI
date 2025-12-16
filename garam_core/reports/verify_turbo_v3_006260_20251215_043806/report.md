# Turbo V3 Verified Result (006260)

## Meta

- Run ID: `verify_turbo_v3_006260_20251215_043806`
- Timestamp (UTC): `2025-12-15T04:38:06Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `006260` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2501, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2621181.9107613824

## Key Points

- Total Return: -97.38%
- Max Drawdown: -97.47%
- Trades: 2501
- Final Equity: 2,621,182 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1250

- Win Rate: 29.44%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00022

- **Expectancy (Net)**: **-0.00258**

- Net PnL Total: -3.22300

- SQN Score: -8.83050


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 282 | 3 | 66.67% | **0.01529** |  |
| TREND_DOWN | 385 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 5740 | 56 | 26.79% | **-0.00419** |  |
| CHOP_LOWVOL | 88221 | 1161 | 29.46% | **-0.00254** |  |
| PANIC | 1251 | 30 | 30.00% | **-0.00294** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00244

- Last 20% Median Exp: -0.00252

- Drop Ratio: -3.02%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
