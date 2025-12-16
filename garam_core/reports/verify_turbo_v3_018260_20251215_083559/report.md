# Turbo V3 Verified Result (018260)

## Meta

- Run ID: `verify_turbo_v3_018260_20251215_083559`
- Timestamp (UTC): `2025-12-15T08:35:59Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `018260` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2592, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1980967.1226785441

## Key Points

- Total Return: -98.02%
- Max Drawdown: -98.02%
- Trades: 2592
- Final Equity: 1,980,967 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1296

- Win Rate: 29.09%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00007

- **Expectancy (Net)**: **-0.00273**

- Net PnL Total: -3.53524

- SQN Score: -15.31284


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 201 | 3 | 33.33% | **-0.00751** |  |
| TREND_DOWN | 247 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 899 | 7 | 14.29% | **-0.00911** |  |
| CHOP_LOWVOL | 93118 | 1265 | 28.93% | **-0.00275** |  |
| PANIC | 1369 | 21 | 42.86% | **0.00161** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00286

- Last 20% Median Exp: -0.00276

- Drop Ratio: 3.18%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
