# Turbo V3 Verified Result (001720)

## Meta

- Run ID: `verify_turbo_v3_001720_20251215_070510`
- Timestamp (UTC): `2025-12-15T07:05:10Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `001720` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2223, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3346639.1781738936

## Key Points

- Total Return: -96.65%
- Max Drawdown: -96.72%
- Trades: 2223
- Final Equity: 3,346,639 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1111

- Win Rate: 26.28%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00023

- **Expectancy (Net)**: **-0.00257**

- Net PnL Total: -2.85362

- SQN Score: -8.46220


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 362 | 1 | 0.00% | **-0.02890** |  |
| TREND_DOWN | 401 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1901 | 11 | 18.18% | **0.00037** |  |
| CHOP_LOWVOL | 71508 | 1064 | 26.22% | **-0.00259** |  |
| PANIC | 1674 | 35 | 31.43% | **-0.00200** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00254

- Last 20% Median Exp: -0.00264

- Drop Ratio: -4.07%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
