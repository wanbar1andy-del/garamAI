# Turbo V3 Verified Result (011790)

## Meta

- Run ID: `verify_turbo_v3_011790_20251215_073230`
- Timestamp (UTC): `2025-12-15T07:32:30Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `011790` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2403, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2910833.096629729

## Key Points

- Total Return: -97.09%
- Max Drawdown: -97.25%
- Trades: 2403
- Final Equity: 2,910,833 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1201

- Win Rate: 25.73%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00016

- **Expectancy (Net)**: **-0.00264**

- Net PnL Total: -3.16827

- SQN Score: -8.36886


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 275 | 2 | 0.00% | **-0.01337** |  |
| TREND_DOWN | 325 | 2 | 100.00% | **0.00126** |  |
| CHOP_HIGHVOL | 2355 | 21 | 42.86% | **0.00152** |  |
| CHOP_LOWVOL | 91577 | 1147 | 25.28% | **-0.00268** |  |
| PANIC | 1306 | 29 | 27.59% | **-0.00341** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00291

- Last 20% Median Exp: -0.00204

- Drop Ratio: 29.93%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
