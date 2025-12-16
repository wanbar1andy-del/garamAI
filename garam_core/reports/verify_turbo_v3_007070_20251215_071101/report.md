# Turbo V3 Verified Result (007070)

## Meta

- Run ID: `verify_turbo_v3_007070_20251215_071101`
- Timestamp (UTC): `2025-12-15T07:11:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `007070` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2636, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1965664.1907936467

## Key Points

- Total Return: -98.03%
- Max Drawdown: -98.14%
- Trades: 2636
- Final Equity: 1,965,664 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1318

- Win Rate: 29.67%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00020

- **Expectancy (Net)**: **-0.00260**

- Net PnL Total: -3.43279

- SQN Score: -18.04473


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 255 | 1 | 100.00% | **0.07441** |  |
| TREND_DOWN | 425 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1471 | 26 | 34.62% | **-0.00232** |  |
| CHOP_LOWVOL | 86030 | 1262 | 29.24% | **-0.00266** |  |
| PANIC | 1442 | 29 | 41.38% | **-0.00316** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00258

- Last 20% Median Exp: -0.00258

- Drop Ratio: -0.09%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
