# Turbo V3 Verified Result (240810)

## Meta

- Run ID: `verify_turbo_v3_240810_20251215_033922`
- Timestamp (UTC): `2025-12-15T03:39:22Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `240810` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2966, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1452868.554027426

## Key Points

- Total Return: -98.55%
- Max Drawdown: -98.55%
- Trades: 2966
- Final Equity: 1,452,869 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1483

- Win Rate: 28.52%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00022

- **Expectancy (Net)**: **-0.00258**

- Net PnL Total: -3.82561

- SQN Score: -11.08673


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 89 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 76 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7278 | 84 | 35.71% | **-0.00102** |  |
| CHOP_LOWVOL | 86728 | 1371 | 27.86% | **-0.00265** |  |
| PANIC | 1008 | 28 | 39.29% | **-0.00382** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00253

- Last 20% Median Exp: -0.00202

- Drop Ratio: 19.88%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
