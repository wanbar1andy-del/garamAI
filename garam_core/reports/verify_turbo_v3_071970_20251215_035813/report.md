# Turbo V3 Verified Result (071970)

## Meta

- Run ID: `verify_turbo_v3_071970_20251215_035813`
- Timestamp (UTC): `2025-12-15T03:58:13Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `071970` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2588, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3572139.8563234955

## Key Points

- Total Return: -96.43%
- Max Drawdown: -96.49%
- Trades: 2588
- Final Equity: 3,572,140 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1294

- Win Rate: 28.83%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00053

- **Expectancy (Net)**: **-0.00227**

- Net PnL Total: -2.93809

- SQN Score: -7.60212


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 176 | 2 | 0.00% | **-0.03540** |  |
| TREND_DOWN | 132 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 13481 | 158 | 25.95% | **-0.00307** |  |
| CHOP_LOWVOL | 80675 | 1106 | 29.02% | **-0.00219** |  |
| PANIC | 1361 | 28 | 39.29% | **0.00124** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00213

- Last 20% Median Exp: -0.00302

- Drop Ratio: -41.57%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
