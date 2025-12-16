# Turbo V3 Verified Result (066570)

## Meta

- Run ID: `verify_turbo_v3_066570_20251215_013453`
- Timestamp (UTC): `2025-12-15T01:34:53Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `066570` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2935, win_rate=0.00%, pnl=None, mdd=0.00%, equity=895383.0146852065

## Key Points

- Total Return: -99.10%
- Max Drawdown: -99.11%
- Trades: 2935
- Final Equity: 895,383 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1467

- Win Rate: 25.63%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00009

- **Expectancy (Net)**: **-0.00289**

- Net PnL Total: -4.23888

- SQN Score: -21.56586


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 91 | 1 | 100.00% | **0.00823** |  |
| TREND_DOWN | 171 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 295 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94607 | 1445 | 25.12% | **-0.00293** |  |
| PANIC | 730 | 21 | 57.14% | **-0.00074** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00289

- Last 20% Median Exp: -0.00291

- Drop Ratio: -0.57%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
