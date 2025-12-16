# Turbo V3 Verified Result (005387)

## Meta

- Run ID: `verify_turbo_v3_005387_20251215_012431`
- Timestamp (UTC): `2025-12-15T01:24:31Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005387` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2589, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2567007.278951056

## Key Points

- Total Return: -97.43%
- Max Drawdown: -97.46%
- Trades: 2589
- Final Equity: 2,567,007 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1294

- Win Rate: 30.22%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00028

- **Expectancy (Net)**: **-0.00252**

- Net PnL Total: -3.25655

- SQN Score: -17.13156


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 526 | 4 | 75.00% | **-0.00053** |  |
| TREND_DOWN | 315 | 2 | 0.00% | **-0.00557** |  |
| CHOP_HIGHVOL | 297 | 1 | 0.00% | **-0.00996** |  |
| CHOP_LOWVOL | 93463 | 1249 | 30.18% | **-0.00250** |  |
| PANIC | 1273 | 38 | 28.95% | **-0.00296** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00274

- Last 20% Median Exp: -0.00166

- Drop Ratio: 39.48%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
