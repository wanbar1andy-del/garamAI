# Turbo V3 Verified Result (035420)

## Meta

- Run ID: `verify_turbo_v3_035420_20251215_005334`
- Timestamp (UTC): `2025-12-15T00:53:34Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `035420` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3093, win_rate=0.00%, pnl=None, mdd=0.00%, equity=493874.3206421848

## Key Points

- Total Return: -99.51%
- Max Drawdown: -99.51%
- Trades: 3093
- Final Equity: 493,874 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1546

- Win Rate: 26.26%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00033

- **Expectancy (Net)**: **-0.00313**

- Net PnL Total: -4.84421

- SQN Score: -19.75014


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 159 | 1 | 0.00% | **-0.02098** |  |
| TREND_DOWN | 117 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1715 | 12 | 33.33% | **-0.00667** |  |
| CHOP_LOWVOL | 92964 | 1509 | 26.11% | **-0.00308** |  |
| PANIC | 856 | 24 | 33.33% | **-0.00410** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00312

- Last 20% Median Exp: -0.00349

- Drop Ratio: -11.87%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
