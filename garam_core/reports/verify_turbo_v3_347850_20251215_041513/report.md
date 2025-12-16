# Turbo V3 Verified Result (347850)

## Meta

- Run ID: `verify_turbo_v3_347850_20251215_041513`
- Timestamp (UTC): `2025-12-15T04:15:13Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `347850` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2451, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2609907.718163776

## Key Points

- Total Return: -97.39%
- Max Drawdown: -97.55%
- Trades: 2451
- Final Equity: 2,609,908 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1225

- Win Rate: 30.61%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00049

- **Expectancy (Net)**: **-0.00231**

- Net PnL Total: -2.83167

- SQN Score: -4.16365


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 399 | 4 | 25.00% | **-0.00087** |  |
| TREND_DOWN | 17 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 24959 | 265 | 32.83% | **-0.00347** |  |
| CHOP_LOWVOL | 68413 | 924 | 29.00% | **-0.00284** |  |
| PANIC | 1530 | 32 | 59.38% | **0.02228** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00204

- Last 20% Median Exp: -0.00187

- Drop Ratio: 8.60%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
