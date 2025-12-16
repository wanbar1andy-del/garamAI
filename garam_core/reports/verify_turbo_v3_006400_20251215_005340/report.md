# Turbo V3 Verified Result (006400)

## Meta

- Run ID: `verify_turbo_v3_006400_20251215_005340`
- Timestamp (UTC): `2025-12-15T00:53:40Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `006400` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2696, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1632761.7773888344

## Key Points

- Total Return: -98.37%
- Max Drawdown: -98.38%
- Trades: 2696
- Final Equity: 1,632,762 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1348

- Win Rate: 27.15%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00011

- **Expectancy (Net)**: **-0.00269**

- Net PnL Total: -3.62536

- SQN Score: -12.39998


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 281 | 1 | 100.00% | **0.00806** |  |
| TREND_DOWN | 399 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2044 | 20 | 40.00% | **0.00082** |  |
| CHOP_LOWVOL | 92101 | 1309 | 26.66% | **-0.00275** |  |
| PANIC | 984 | 18 | 44.44% | **-0.00295** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00287

- Last 20% Median Exp: -0.00190

- Drop Ratio: 33.70%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
