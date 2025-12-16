# Turbo V3 Verified Result (006800)

## Meta

- Run ID: `verify_turbo_v3_006800_20251215_010317`
- Timestamp (UTC): `2025-12-15T01:03:17Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `006800` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2826, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2847730.71370709

## Key Points

- Total Return: -97.15%
- Max Drawdown: -97.17%
- Trades: 2826
- Final Equity: 2,847,731 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1413

- Win Rate: 27.88%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00064

- **Expectancy (Net)**: **-0.00216**

- Net PnL Total: -3.05508

- SQN Score: -7.12796


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 347 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 139 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 8019 | 74 | 25.68% | **-0.00181** |  |
| CHOP_LOWVOL | 86022 | 1317 | 28.09% | **-0.00211** |  |
| PANIC | 1116 | 22 | 22.73% | **-0.00657** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00220

- Last 20% Median Exp: -0.00160

- Drop Ratio: 27.04%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
