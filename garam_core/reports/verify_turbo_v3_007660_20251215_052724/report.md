# Turbo V3 Verified Result (007660)

## Meta

- Run ID: `verify_turbo_v3_007660_20251215_052724`
- Timestamp (UTC): `2025-12-15T05:27:24Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `007660` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2484, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1948669.222771221

## Key Points

- Total Return: -98.05%
- Max Drawdown: -98.06%
- Trades: 2484
- Final Equity: 1,948,669 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1242

- Win Rate: 27.70%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00015

- **Expectancy (Net)**: **-0.00295**

- Net PnL Total: -3.66169

- SQN Score: -8.15177


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 454 | 8 | 25.00% | **-0.01576** |  |
| TREND_DOWN | 157 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 12387 | 113 | 33.63% | **-0.00412** |  |
| CHOP_LOWVOL | 81616 | 1096 | 26.92% | **-0.00277** |  |
| PANIC | 1257 | 25 | 36.00% | **-0.00145** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00315

- Last 20% Median Exp: -0.00211

- Drop Ratio: 32.91%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
