# Turbo V3 Verified Result (282330)

## Meta

- Run ID: `verify_turbo_v3_282330_20251215_073215`
- Timestamp (UTC): `2025-12-15T07:32:15Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `282330` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3012, win_rate=0.00%, pnl=None, mdd=0.00%, equity=761792.3510251465

## Key Points

- Total Return: -99.24%
- Max Drawdown: -99.26%
- Trades: 3012
- Final Equity: 761,792 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1506

- Win Rate: 27.16%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00020

- **Expectancy (Net)**: **-0.00300**

- Net PnL Total: -4.51447

- SQN Score: -24.03990


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 108 | 1 | 0.00% | **-0.02454** |  |
| TREND_DOWN | 119 | 2 | 0.00% | **-0.00329** |  |
| CHOP_HIGHVOL | 405 | 3 | 66.67% | **-0.00214** |  |
| CHOP_LOWVOL | 92698 | 1468 | 26.91% | **-0.00297** |  |
| PANIC | 1483 | 32 | 37.50% | **-0.00387** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00298

- Last 20% Median Exp: -0.00312

- Drop Ratio: -4.61%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
