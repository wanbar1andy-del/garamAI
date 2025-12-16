# Turbo V3 Verified Result (001740)

## Meta

- Run ID: `verify_turbo_v3_001740_20251215_100241`
- Timestamp (UTC): `2025-12-15T10:02:41Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `001740` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3218, win_rate=0.00%, pnl=None, mdd=0.00%, equity=431230.6404548698

## Key Points

- Total Return: -99.57%
- Max Drawdown: -99.57%
- Trades: 3218
- Final Equity: 431,231 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1609

- Win Rate: 24.80%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00030

- **Expectancy (Net)**: **-0.00310**

- Net PnL Total: -4.99066

- SQN Score: -32.66182


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 37 | 1 | 100.00% | **-0.00165** |  |
| TREND_DOWN | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 38 | 1 | 100.00% | **-0.00169** |  |
| CHOP_LOWVOL | 88479 | 1573 | 24.48% | **-0.00313** |  |
| PANIC | 1265 | 34 | 35.29% | **-0.00197** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00308

- Last 20% Median Exp: -0.00300

- Drop Ratio: 2.44%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
