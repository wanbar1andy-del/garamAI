# Turbo V3 Verified Result (336260)

## Meta

- Run ID: `verify_turbo_v3_336260_20251215_070918`
- Timestamp (UTC): `2025-12-15T07:09:18Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `336260` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2559, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1900473.8334012614

## Key Points

- Total Return: -98.10%
- Max Drawdown: -98.15%
- Trades: 2559
- Final Equity: 1,900,474 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1279

- Win Rate: 27.76%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00002

- **Expectancy (Net)**: **-0.00282**

- Net PnL Total: -3.60419

- SQN Score: -9.44794


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 159 | 6 | 33.33% | **-0.01143** |  |
| TREND_DOWN | 232 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7170 | 62 | 25.81% | **-0.00217** |  |
| CHOP_LOWVOL | 85856 | 1188 | 27.86% | **-0.00285** |  |
| PANIC | 1458 | 23 | 26.09% | **-0.00057** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00261

- Last 20% Median Exp: -0.00352

- Drop Ratio: -34.97%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
