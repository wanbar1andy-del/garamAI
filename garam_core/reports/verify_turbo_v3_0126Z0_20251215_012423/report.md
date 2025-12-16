# Turbo V3 Verified Result (0126Z0)

## Meta

- Run ID: `verify_turbo_v3_0126Z0_20251215_012423`
- Timestamp (UTC): `2025-12-15T01:24:23Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `0126Z0` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=126, win_rate=0.00%, pnl=None, mdd=0.00%, equity=128897666.41613092

## Key Points

- Total Return: 28.90%
- Max Drawdown: -17.11%
- Trades: 126
- Final Equity: 128,897,666 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 63

- Win Rate: 30.16%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00616

- **Expectancy (Net)**: **0.00336**

- Net PnL Total: 0.21141

- SQN Score: 0.86571


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 1 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 14 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4360 | 40 | 35.00% | **0.00536** |  |
| CHOP_LOWVOL | 1332 | 21 | 19.05% | **-0.00280** |  |
| PANIC | 87 | 2 | 50.00% | **0.02781** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: 0.00000

- Last 20% Median Exp: 0.00000

- Drop Ratio: 0.00%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
