# Turbo V3 Verified Result (041510)

## Meta

- Run ID: `verify_turbo_v3_041510_20251215_072349`
- Timestamp (UTC): `2025-12-15T07:23:49Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `041510` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2646, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2352372.6814158023

## Key Points

- Total Return: -97.65%
- Max Drawdown: -97.65%
- Trades: 2646
- Final Equity: 2,352,373 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1323

- Win Rate: 30.31%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00035

- **Expectancy (Net)**: **-0.00245**

- Net PnL Total: -3.24732

- SQN Score: -11.06790


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 150 | 1 | 0.00% | **-0.00848** |  |
| TREND_DOWN | 112 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3112 | 35 | 28.57% | **-0.00357** |  |
| CHOP_LOWVOL | 91038 | 1262 | 30.27% | **-0.00238** |  |
| PANIC | 1446 | 25 | 36.00% | **-0.00455** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00203

- Last 20% Median Exp: -0.00294

- Drop Ratio: -44.59%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
