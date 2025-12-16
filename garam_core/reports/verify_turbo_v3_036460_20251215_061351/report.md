# Turbo V3 Verified Result (036460)

## Meta

- Run ID: `verify_turbo_v3_036460_20251215_061351`
- Timestamp (UTC): `2025-12-15T06:13:51Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `036460` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2910, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1263240.211444279

## Key Points

- Total Return: -98.74%
- Max Drawdown: -98.74%
- Trades: 2910
- Final Equity: 1,263,240 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1455

- Win Rate: 27.63%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00011

- **Expectancy (Net)**: **-0.00269**

- Net PnL Total: -3.91752

- SQN Score: -16.63794


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 109 | 3 | 66.67% | **-0.00389** |  |
| TREND_DOWN | 300 | 1 | 0.00% | **-0.00761** |  |
| CHOP_HIGHVOL | 1880 | 19 | 26.32% | **-0.00426** |  |
| CHOP_LOWVOL | 92596 | 1405 | 27.54% | **-0.00277** |  |
| PANIC | 971 | 27 | 29.63% | **0.00261** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00263

- Last 20% Median Exp: -0.00253

- Drop Ratio: 3.56%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
