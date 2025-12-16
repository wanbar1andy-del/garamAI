# Turbo V3 Verified Result (226950)

## Meta

- Run ID: `verify_turbo_v3_226950_20251215_081427`
- Timestamp (UTC): `2025-12-15T08:14:27Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `226950` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2292, win_rate=0.00%, pnl=None, mdd=0.00%, equity=6142254.8310999125

## Key Points

- Total Return: -93.86%
- Max Drawdown: -95.44%
- Trades: 2292
- Final Equity: 6,142,255 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1146

- Win Rate: 29.93%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00094

- **Expectancy (Net)**: **-0.00186**

- Net PnL Total: -2.12750

- SQN Score: -2.69196


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 448 | 1 | 100.00% | **0.49533** |  |
| TREND_DOWN | 165 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 27390 | 280 | 28.21% | **-0.00351** |  |
| CHOP_LOWVOL | 65382 | 826 | 30.27% | **-0.00170** |  |
| PANIC | 1714 | 39 | 33.33% | **-0.00598** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00202

- Last 20% Median Exp: -0.00200

- Drop Ratio: 1.13%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
