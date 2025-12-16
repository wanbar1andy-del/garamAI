# Turbo V3 Verified Result (042670)

## Meta

- Run ID: `verify_turbo_v3_042670_20251215_054414`
- Timestamp (UTC): `2025-12-15T05:44:14Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `042670` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2678, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2344476.9133415273

## Key Points

- Total Return: -97.66%
- Max Drawdown: -97.76%
- Trades: 2678
- Final Equity: 2,344,477 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1339

- Win Rate: 27.86%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00046

- **Expectancy (Net)**: **-0.00234**

- Net PnL Total: -3.13380

- SQN Score: -7.30828


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 339 | 2 | 50.00% | **0.01003** |  |
| TREND_DOWN | 165 | 1 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 3420 | 28 | 35.71% | **-0.00515** |  |
| CHOP_LOWVOL | 90727 | 1281 | 27.40% | **-0.00234** |  |
| PANIC | 1222 | 27 | 40.74% | **-0.00024** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00241

- Last 20% Median Exp: -0.00273

- Drop Ratio: -13.20%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
