# Turbo V3 Verified Result (005830)

## Meta

- Run ID: `verify_turbo_v3_005830_20251215_051708`
- Timestamp (UTC): `2025-12-15T05:17:08Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005830` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2794, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1083651.8186994507

## Key Points

- Total Return: -98.92%
- Max Drawdown: -98.92%
- Trades: 2794
- Final Equity: 1,083,652 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1397

- Win Rate: 28.27%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00020

- **Expectancy (Net)**: **-0.00300**

- Net PnL Total: -4.18490

- SQN Score: -19.66340


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 105 | 1 | 0.00% | **-0.00331** |  |
| TREND_DOWN | 273 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 119 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 93789 | 1370 | 28.10% | **-0.00298** |  |
| PANIC | 1502 | 26 | 38.46% | **-0.00365** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00311

- Last 20% Median Exp: -0.00264

- Drop Ratio: 15.07%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
