# Turbo V3 Verified Result (361610)

## Meta

- Run ID: `verify_turbo_v3_361610_20251215_080845`
- Timestamp (UTC): `2025-12-15T08:08:45Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `361610` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2690, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1805885.8886626149

## Key Points

- Total Return: -98.19%
- Max Drawdown: -98.20%
- Trades: 2690
- Final Equity: 1,805,886 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1345

- Win Rate: 26.02%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00001

- **Expectancy (Net)**: **-0.00279**

- Net PnL Total: -3.75915

- SQN Score: -12.38788


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 50 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 101 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2697 | 19 | 31.58% | **-0.00235** |  |
| CHOP_LOWVOL | 90417 | 1297 | 25.75% | **-0.00276** |  |
| PANIC | 1068 | 29 | 34.48% | **-0.00479** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00271

- Last 20% Median Exp: -0.00286

- Drop Ratio: -5.74%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
