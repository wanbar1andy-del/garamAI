# Turbo V3 Verified Result (285130)

## Meta

- Run ID: `verify_turbo_v3_285130_20251215_094705`
- Timestamp (UTC): `2025-12-15T09:47:05Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `285130` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2715, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1707872.4325293445

## Key Points

- Total Return: -98.29%
- Max Drawdown: -98.31%
- Trades: 2715
- Final Equity: 1,707,872 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1357

- Win Rate: 25.57%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00002

- **Expectancy (Net)**: **-0.00278**

- Net PnL Total: -3.77723

- SQN Score: -11.25277


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 251 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 200 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1255 | 12 | 33.33% | **0.00295** |  |
| CHOP_LOWVOL | 86624 | 1318 | 25.04% | **-0.00286** |  |
| PANIC | 1228 | 27 | 48.15% | **-0.00136** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00284

- Last 20% Median Exp: -0.00263

- Drop Ratio: 7.21%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
