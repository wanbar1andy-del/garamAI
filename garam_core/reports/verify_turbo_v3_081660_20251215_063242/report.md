# Turbo V3 Verified Result (081660)

## Meta

- Run ID: `verify_turbo_v3_081660_20251215_063242`
- Timestamp (UTC): `2025-12-15T06:32:42Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `081660` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3121, win_rate=0.00%, pnl=None, mdd=0.00%, equity=499512.763382051

## Key Points

- Total Return: -99.50%
- Max Drawdown: -99.52%
- Trades: 3121
- Final Equity: 499,513 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1560

- Win Rate: 25.58%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00034

- **Expectancy (Net)**: **-0.00314**

- Net PnL Total: -4.90213

- SQN Score: -24.14998


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 39 | 1 | 0.00% | **-0.00876** |  |
| TREND_DOWN | 55 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 281 | 1 | 0.00% | **-0.00604** |  |
| CHOP_LOWVOL | 93061 | 1526 | 25.23% | **-0.00316** |  |
| PANIC | 1491 | 32 | 43.75% | **-0.00219** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00314

- Last 20% Median Exp: -0.00351

- Drop Ratio: -11.75%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
