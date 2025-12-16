# Turbo V3 Verified Result (024110)

## Meta

- Run ID: `verify_turbo_v3_024110_20251215_010338`
- Timestamp (UTC): `2025-12-15T01:03:38Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `024110` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3201, win_rate=0.00%, pnl=None, mdd=0.00%, equity=790825.018886154

## Key Points

- Total Return: -99.21%
- Max Drawdown: -99.21%
- Trades: 3201
- Final Equity: 790,825 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1600

- Win Rate: 27.62%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00004

- **Expectancy (Net)**: **-0.00276**

- Net PnL Total: -4.41986

- SQN Score: -30.52568


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 326 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 157 | 1 | 100.00% | **0.00064** |  |
| CHOP_HIGHVOL | 110 | 2 | 50.00% | **-0.00581** |  |
| CHOP_LOWVOL | 94077 | 1565 | 27.09% | **-0.00280** |  |
| PANIC | 1093 | 32 | 50.00% | **-0.00101** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00272

- Last 20% Median Exp: -0.00296

- Drop Ratio: -8.76%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
