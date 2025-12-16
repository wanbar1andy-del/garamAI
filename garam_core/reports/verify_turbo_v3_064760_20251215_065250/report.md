# Turbo V3 Verified Result (064760)

## Meta

- Run ID: `verify_turbo_v3_064760_20251215_065250`
- Timestamp (UTC): `2025-12-15T06:52:50Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `064760` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2656, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1499820.635642336

## Key Points

- Total Return: -98.50%
- Max Drawdown: -98.50%
- Trades: 2656
- Final Equity: 1,499,821 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1328

- Win Rate: 29.82%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00003

- **Expectancy (Net)**: **-0.00283**

- Net PnL Total: -3.76148

- SQN Score: -11.87519


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 146 | 1 | 100.00% | **0.02074** |  |
| TREND_DOWN | 39 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4129 | 53 | 30.19% | **-0.00311** |  |
| CHOP_LOWVOL | 87323 | 1249 | 29.86% | **-0.00275** |  |
| PANIC | 1448 | 25 | 24.00% | **-0.00712** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00270

- Last 20% Median Exp: -0.00288

- Drop Ratio: -6.69%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
