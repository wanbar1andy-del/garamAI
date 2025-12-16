# Turbo V3 Verified Result (034730)

## Meta

- Run ID: `verify_turbo_v3_034730_20251215_054043`
- Timestamp (UTC): `2025-12-15T05:40:43Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `034730` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2817, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1741224.4026306134

## Key Points

- Total Return: -98.26%
- Max Drawdown: -98.28%
- Trades: 2817
- Final Equity: 1,741,224 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1408

- Win Rate: 28.20%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00025

- **Expectancy (Net)**: **-0.00255**

- Net PnL Total: -3.59711

- SQN Score: -11.32821


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 427 | 2 | 0.00% | **-0.00605** |  |
| TREND_DOWN | 215 | 3 | 0.00% | **-0.00306** |  |
| CHOP_HIGHVOL | 3001 | 27 | 25.93% | **-0.00195** |  |
| CHOP_LOWVOL | 91027 | 1349 | 28.32% | **-0.00253** |  |
| PANIC | 1179 | 27 | 29.63% | **-0.00388** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00267

- Last 20% Median Exp: -0.00219

- Drop Ratio: 18.03%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
