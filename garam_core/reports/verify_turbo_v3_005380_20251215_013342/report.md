# Turbo V3 Verified Result (005380)

## Meta

- Run ID: `verify_turbo_v3_005380_20251215_013342`
- Timestamp (UTC): `2025-12-15T01:33:42Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005380` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3360, win_rate=0.00%, pnl=None, mdd=0.00%, equity=501859.44161365944

## Key Points

- Total Return: -99.50%
- Max Drawdown: -99.50%
- Trades: 3360
- Final Equity: 501,859 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1680

- Win Rate: 26.73%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00001

- **Expectancy (Net)**: **-0.00279**

- Net PnL Total: -4.68673

- SQN Score: -22.35942


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 426 | 2 | 50.00% | **-0.00463** |  |
| TREND_DOWN | 418 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 645 | 2 | 50.00% | **-0.00390** |  |
| CHOP_LOWVOL | 93723 | 1658 | 26.54% | **-0.00282** |  |
| PANIC | 679 | 18 | 38.89% | **0.00071** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00291

- Last 20% Median Exp: -0.00255

- Drop Ratio: 12.33%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
