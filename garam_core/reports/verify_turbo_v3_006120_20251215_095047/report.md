# Turbo V3 Verified Result (006120)

## Meta

- Run ID: `verify_turbo_v3_006120_20251215_095047`
- Timestamp (UTC): `2025-12-15T09:50:47Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `006120` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2326, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4016119.038026741

## Key Points

- Total Return: -95.98%
- Max Drawdown: -96.00%
- Trades: 2326
- Final Equity: 4,016,119 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1163

- Win Rate: 28.46%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00023

- **Expectancy (Net)**: **-0.00257**

- Net PnL Total: -2.98725

- SQN Score: -16.03618


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 76 | 1 | 100.00% | **0.00536** |  |
| TREND_DOWN | 87 | 1 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 187 | 1 | 0.00% | **-0.01172** |  |
| CHOP_LOWVOL | 77452 | 1140 | 28.68% | **-0.00252** |  |
| PANIC | 1320 | 20 | 15.00% | **-0.00555** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00269

- Last 20% Median Exp: -0.00278

- Drop Ratio: -3.42%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
