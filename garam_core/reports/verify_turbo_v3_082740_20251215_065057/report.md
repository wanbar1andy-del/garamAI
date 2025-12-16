# Turbo V3 Verified Result (082740)

## Meta

- Run ID: `verify_turbo_v3_082740_20251215_065057`
- Timestamp (UTC): `2025-12-15T06:50:57Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `082740` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2624, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1841248.9282974931

## Key Points

- Total Return: -98.16%
- Max Drawdown: -98.17%
- Trades: 2624
- Final Equity: 1,841,249 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1312

- Win Rate: 29.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00021

- **Expectancy (Net)**: **-0.00259**

- Net PnL Total: -3.39448

- SQN Score: -8.87454


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 99 | 2 | 0.00% | **-0.02817** |  |
| TREND_DOWN | 38 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 11413 | 107 | 36.45% | **-0.00145** |  |
| CHOP_LOWVOL | 83062 | 1175 | 28.77% | **-0.00264** |  |
| PANIC | 1273 | 28 | 35.71% | **-0.00276** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00227

- Last 20% Median Exp: -0.00340

- Drop Ratio: -49.82%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
