# Turbo V3 Verified Result (000155)

## Meta

- Run ID: `verify_turbo_v3_000155_20251215_064612`
- Timestamp (UTC): `2025-12-15T06:46:12Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000155` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2376, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3246225.0148484414

## Key Points

- Total Return: -96.75%
- Max Drawdown: -96.80%
- Trades: 2376
- Final Equity: 3,246,225 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1188

- Win Rate: 28.79%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00025

- **Expectancy (Net)**: **-0.00255**

- Net PnL Total: -3.02913

- SQN Score: -7.09929


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 201 | 5 | 20.00% | **-0.00346** |  |
| TREND_DOWN | 68 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7731 | 77 | 31.17% | **-0.00403** |  |
| CHOP_LOWVOL | 74895 | 1066 | 28.71% | **-0.00240** |  |
| PANIC | 1466 | 40 | 27.50% | **-0.00369** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00269

- Last 20% Median Exp: -0.00237

- Drop Ratio: 11.80%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
