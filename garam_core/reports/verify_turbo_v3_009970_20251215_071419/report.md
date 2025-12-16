# Turbo V3 Verified Result (009970)

## Meta

- Run ID: `verify_turbo_v3_009970_20251215_071419`
- Timestamp (UTC): `2025-12-15T07:14:19Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `009970` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2917, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1069775.374270239

## Key Points

- Total Return: -98.93%
- Max Drawdown: -98.94%
- Trades: 2917
- Final Equity: 1,069,775 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1458

- Win Rate: 29.36%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00013

- **Expectancy (Net)**: **-0.00293**

- Net PnL Total: -4.27594

- SQN Score: -18.28787


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 133 | 1 | 100.00% | **0.02470** |  |
| TREND_DOWN | 70 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2648 | 35 | 40.00% | **-0.00151** |  |
| CHOP_LOWVOL | 84055 | 1376 | 28.71% | **-0.00301** |  |
| PANIC | 1970 | 46 | 39.13% | **-0.00243** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00294

- Last 20% Median Exp: -0.00315

- Drop Ratio: -7.21%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
