# Turbo V3 Verified Result (006280)

## Meta

- Run ID: `verify_turbo_v3_006280_20251215_080441`
- Timestamp (UTC): `2025-12-15T08:04:41Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `006280` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2730, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2213160.3508277982

## Key Points

- Total Return: -97.79%
- Max Drawdown: -97.87%
- Trades: 2730
- Final Equity: 2,213,160 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1365

- Win Rate: 32.01%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00034

- **Expectancy (Net)**: **-0.00246**

- Net PnL Total: -3.36041

- SQN Score: -15.66432


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 97 | 2 | 100.00% | **0.00919** |  |
| TREND_DOWN | 137 | 1 | 0.00% | **-0.00485** |  |
| CHOP_HIGHVOL | 676 | 7 | 42.86% | **-0.00409** |  |
| CHOP_LOWVOL | 91868 | 1328 | 32.00% | **-0.00244** |  |
| PANIC | 1485 | 27 | 25.93% | **-0.00378** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00255

- Last 20% Median Exp: -0.00249

- Drop Ratio: 2.44%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
