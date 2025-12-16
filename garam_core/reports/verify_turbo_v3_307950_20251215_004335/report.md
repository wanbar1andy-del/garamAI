# Turbo V3 Verified Result (307950)

## Meta

- Run ID: `verify_turbo_v3_307950_20251215_004335`
- Timestamp (UTC): `2025-12-15T00:43:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `307950` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2457, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2789431.767908163

## Key Points

- Total Return: -97.21%
- Max Drawdown: -97.23%
- Trades: 2457
- Final Equity: 2,789,432 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1228

- Win Rate: 30.13%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00029

- **Expectancy (Net)**: **-0.00251**

- Net PnL Total: -3.08181

- SQN Score: -9.77722


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 404 | 8 | 50.00% | **0.02898** |  |
| TREND_DOWN | 261 | 1 | 100.00% | **0.00305** |  |
| CHOP_HIGHVOL | 3036 | 32 | 21.88% | **-0.00415** |  |
| CHOP_LOWVOL | 90017 | 1158 | 29.71% | **-0.00275** |  |
| PANIC | 1487 | 29 | 48.28% | **-0.00014** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00246

- Last 20% Median Exp: -0.00300

- Drop Ratio: -22.00%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
