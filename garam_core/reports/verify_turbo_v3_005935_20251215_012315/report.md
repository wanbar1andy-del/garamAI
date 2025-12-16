# Turbo V3 Verified Result (005935)

## Meta

- Run ID: `verify_turbo_v3_005935_20251215_012315`
- Timestamp (UTC): `2025-12-15T01:23:15Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005935` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3219, win_rate=0.00%, pnl=None, mdd=0.00%, equity=808666.6765806066

## Key Points

- Total Return: -99.19%
- Max Drawdown: -99.20%
- Trades: 3219
- Final Equity: 808,667 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1609

- Win Rate: 28.15%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00017

- **Expectancy (Net)**: **-0.00263**

- Net PnL Total: -4.23129

- SQN Score: -22.44198


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 474 | 3 | 66.67% | **-0.00199** |  |
| TREND_DOWN | 86 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 58 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94532 | 1584 | 27.71% | **-0.00264** |  |
| PANIC | 746 | 22 | 54.55% | **-0.00186** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00278

- Last 20% Median Exp: -0.00230

- Drop Ratio: 17.14%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
