# Turbo V3 Verified Result (035250)

## Meta

- Run ID: `verify_turbo_v3_035250_20251215_072429`
- Timestamp (UTC): `2025-12-15T07:24:29Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `035250` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2860, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1205113.7487602488

## Key Points

- Total Return: -98.79%
- Max Drawdown: -98.80%
- Trades: 2860
- Final Equity: 1,205,114 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1430

- Win Rate: 28.74%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -4.08717

- SQN Score: -36.02142


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 61 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 155 | 1 | 100.00% | **-0.00086** |  |
| CHOP_HIGHVOL | 14 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94190 | 1399 | 28.45% | **-0.00288** |  |
| PANIC | 1314 | 30 | 40.00% | **-0.00193** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00287

- Last 20% Median Exp: -0.00298

- Drop Ratio: -3.71%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
