# Turbo V3 Verified Result (010060)

## Meta

- Run ID: `verify_turbo_v3_010060_20251215_091135`
- Timestamp (UTC): `2025-12-15T09:11:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `010060` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2748, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1917713.036271548

## Key Points

- Total Return: -98.08%
- Max Drawdown: -98.10%
- Trades: 2748
- Final Equity: 1,917,713 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1374

- Win Rate: 27.44%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00013

- **Expectancy (Net)**: **-0.00267**

- Net PnL Total: -3.67421

- SQN Score: -10.18058


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 425 | 4 | 25.00% | **-0.01176** |  |
| TREND_DOWN | 235 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 5018 | 54 | 38.89% | **-0.00091** |  |
| CHOP_LOWVOL | 88441 | 1292 | 27.01% | **-0.00280** |  |
| PANIC | 1310 | 24 | 25.00% | **0.00147** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00255

- Last 20% Median Exp: -0.00271

- Drop Ratio: -6.40%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
