# Turbo V3 Verified Result (005385)

## Meta

- Run ID: `verify_turbo_v3_005385_20251215_040228`
- Timestamp (UTC): `2025-12-15T04:02:28Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005385` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2895, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1331445.4990678853

## Key Points

- Total Return: -98.67%
- Max Drawdown: -98.68%
- Trades: 2895
- Final Equity: 1,331,445 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1447

- Win Rate: 29.85%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00016

- **Expectancy (Net)**: **-0.00264**

- Net PnL Total: -3.81372

- SQN Score: -21.58237


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 248 | 4 | 50.00% | **0.00248** |  |
| TREND_DOWN | 196 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 17 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 93383 | 1415 | 29.61% | **-0.00267** |  |
| PANIC | 1248 | 28 | 39.29% | **-0.00163** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00284

- Last 20% Median Exp: -0.00174

- Drop Ratio: 38.66%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
