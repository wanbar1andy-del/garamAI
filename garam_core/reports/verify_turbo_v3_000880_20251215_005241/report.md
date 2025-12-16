# Turbo V3 Verified Result (000880)

## Meta

- Run ID: `verify_turbo_v3_000880_20251215_005241`
- Timestamp (UTC): `2025-12-15T00:52:41Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000880` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2671, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2178203.416869096

## Key Points

- Total Return: -97.82%
- Max Drawdown: -97.83%
- Trades: 2671
- Final Equity: 2,178,203 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1335

- Win Rate: 29.66%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00033

- **Expectancy (Net)**: **-0.00247**

- Net PnL Total: -3.29400

- SQN Score: -8.61546


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 263 | 4 | 50.00% | **0.01635** |  |
| TREND_DOWN | 285 | 1 | 100.00% | **0.00256** |  |
| CHOP_HIGHVOL | 6663 | 65 | 38.46% | **-0.00371** |  |
| CHOP_LOWVOL | 86114 | 1246 | 28.97% | **-0.00241** |  |
| PANIC | 1239 | 19 | 36.84% | **-0.00600** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00250

- Last 20% Median Exp: -0.00346

- Drop Ratio: -38.29%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
