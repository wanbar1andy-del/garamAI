# Turbo V3 Verified Result (376900)

## Meta

- Run ID: `verify_turbo_v3_376900_20251215_100558`
- Timestamp (UTC): `2025-12-15T10:05:58Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `376900` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=1362, win_rate=0.00%, pnl=None, mdd=0.00%, equity=22411916.99627435

## Key Points

- Total Return: -77.59%
- Max Drawdown: -80.56%
- Trades: 1362
- Final Equity: 22,411,917 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 681

- Win Rate: 25.84%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00108

- **Expectancy (Net)**: **-0.00172**

- Net PnL Total: -1.16887

- SQN Score: -1.99295


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 189 | 1 | 100.00% | **0.02923** |  |
| TREND_DOWN | 87 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 19325 | 217 | 27.65% | **0.00033** |  |
| CHOP_LOWVOL | 34779 | 441 | 24.72% | **-0.00288** |  |
| PANIC | 1030 | 22 | 27.27% | **0.00011** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00273

- Last 20% Median Exp: 0.00088

- Drop Ratio: 132.28%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
