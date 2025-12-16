# Turbo V3 Verified Result (023530)

## Meta

- Run ID: `verify_turbo_v3_023530_20251215_091421`
- Timestamp (UTC): `2025-12-15T09:14:21Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `023530` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3468, win_rate=0.00%, pnl=None, mdd=0.00%, equity=639282.1640121446

## Key Points

- Total Return: -99.36%
- Max Drawdown: -99.37%
- Trades: 3468
- Final Equity: 639,282 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1734

- Win Rate: 29.70%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00021

- **Expectancy (Net)**: **-0.00259**

- Net PnL Total: -4.48318

- SQN Score: -22.68160


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 89 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 36 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1065 | 10 | 60.00% | **-0.00228** |  |
| CHOP_LOWVOL | 92104 | 1699 | 29.31% | **-0.00257** |  |
| PANIC | 989 | 25 | 44.00% | **-0.00400** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00260

- Last 20% Median Exp: -0.00293

- Drop Ratio: -13.01%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
