# Turbo V3 Verified Result (088350)

## Meta

- Run ID: `verify_turbo_v3_088350_20251215_065918`
- Timestamp (UTC): `2025-12-15T06:59:18Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `088350` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3300, win_rate=0.00%, pnl=None, mdd=0.00%, equity=743764.0823762808

## Key Points

- Total Return: -99.26%
- Max Drawdown: -99.26%
- Trades: 3300
- Final Equity: 743,764 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1650

- Win Rate: 23.94%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00004

- **Expectancy (Net)**: **-0.00276**

- Net PnL Total: -4.54622

- SQN Score: -18.01948


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 115 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 21 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 867 | 5 | 80.00% | **0.00106** |  |
| CHOP_LOWVOL | 92885 | 1630 | 23.87% | **-0.00276** |  |
| PANIC | 834 | 15 | 13.33% | **-0.00388** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00282

- Last 20% Median Exp: -0.00274

- Drop Ratio: 2.59%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
