# Turbo V3 Verified Result (039030)

## Meta

- Run ID: `verify_turbo_v3_039030_20251215_041533`
- Timestamp (UTC): `2025-12-15T04:15:33Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `039030` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2569, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2040479.1748135707

## Key Points

- Total Return: -97.96%
- Max Drawdown: -98.15%
- Trades: 2569
- Final Equity: 2,040,479 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1284

- Win Rate: 26.01%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00014

- **Expectancy (Net)**: **-0.00266**

- Net PnL Total: -3.41968

- SQN Score: -7.41061


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 401 | 2 | 50.00% | **-0.00661** |  |
| TREND_DOWN | 195 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 8970 | 90 | 26.67% | **-0.00440** |  |
| CHOP_LOWVOL | 84920 | 1165 | 25.49% | **-0.00263** |  |
| PANIC | 1235 | 27 | 44.44% | **0.00198** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00272

- Last 20% Median Exp: -0.00276

- Drop Ratio: -1.29%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
