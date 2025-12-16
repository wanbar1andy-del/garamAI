# Turbo V3 Verified Result (028260)

## Meta

- Run ID: `verify_turbo_v3_028260_20251215_045719`
- Timestamp (UTC): `2025-12-15T04:57:19Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `028260` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2677, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2086966.8270854258

## Key Points

- Total Return: -97.91%
- Max Drawdown: -97.93%
- Trades: 2677
- Final Equity: 2,086,967 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1338

- Win Rate: 29.30%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00019

- **Expectancy (Net)**: **-0.00261**

- Net PnL Total: -3.48669

- SQN Score: -11.85324


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 328 | 2 | 0.00% | **-0.01663** |  |
| TREND_DOWN | 111 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1756 | 14 | 21.43% | **-0.00449** |  |
| CHOP_LOWVOL | 92448 | 1300 | 29.38% | **-0.00256** |  |
| PANIC | 1231 | 22 | 31.82% | **-0.00257** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00264

- Last 20% Median Exp: -0.00240

- Drop Ratio: 9.00%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
