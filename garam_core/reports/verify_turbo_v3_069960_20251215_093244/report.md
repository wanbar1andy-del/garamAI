# Turbo V3 Verified Result (069960)

## Meta

- Run ID: `verify_turbo_v3_069960_20251215_093244`
- Timestamp (UTC): `2025-12-15T09:32:44Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `069960` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3220, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1169402.0985143061

## Key Points

- Total Return: -98.83%
- Max Drawdown: -98.90%
- Trades: 3220
- Final Equity: 1,169,402 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1610

- Win Rate: 30.56%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00026

- **Expectancy (Net)**: **-0.00254**

- Net PnL Total: -4.08574

- SQN Score: -16.41016


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 232 | 1 | 0.00% | **-0.00382** |  |
| TREND_DOWN | 4 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3345 | 40 | 32.50% | **-0.00252** |  |
| CHOP_LOWVOL | 90489 | 1547 | 30.12% | **-0.00266** |  |
| PANIC | 1213 | 22 | 59.09% | **0.00617** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00248

- Last 20% Median Exp: -0.00298

- Drop Ratio: -20.23%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
