# Turbo V3 Verified Result (009150)

## Meta

- Run ID: `verify_turbo_v3_009150_20251215_063126`
- Timestamp (UTC): `2025-12-15T06:31:26Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `009150` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2634, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2828630.250258679

## Key Points

- Total Return: -97.17%
- Max Drawdown: -97.20%
- Trades: 2634
- Final Equity: 2,828,630 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1317

- Win Rate: 27.56%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00030

- **Expectancy (Net)**: **-0.00250**

- Net PnL Total: -3.29770

- SQN Score: -10.49660


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 657 | 3 | 66.67% | **-0.00041** |  |
| TREND_DOWN | 262 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2975 | 35 | 28.57% | **-0.00218** |  |
| CHOP_LOWVOL | 90878 | 1253 | 27.37% | **-0.00246** |  |
| PANIC | 1123 | 26 | 30.77% | **-0.00506** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00235

- Last 20% Median Exp: -0.00274

- Drop Ratio: -16.53%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
