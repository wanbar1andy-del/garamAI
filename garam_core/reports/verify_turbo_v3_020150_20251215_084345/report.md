# Turbo V3 Verified Result (020150)

## Meta

- Run ID: `verify_turbo_v3_020150_20251215_084345`
- Timestamp (UTC): `2025-12-15T08:43:45Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `020150` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2616, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2527304.6214832054

## Key Points

- Total Return: -97.47%
- Max Drawdown: -97.48%
- Trades: 2616
- Final Equity: 2,527,305 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1308

- Win Rate: 26.53%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00031

- **Expectancy (Net)**: **-0.00249**

- Net PnL Total: -3.25756

- SQN Score: -6.99945


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 177 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 67 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7030 | 77 | 32.47% | **0.00018** |  |
| CHOP_LOWVOL | 81456 | 1202 | 25.79% | **-0.00269** |  |
| PANIC | 1108 | 29 | 41.38% | **-0.00117** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00283

- Last 20% Median Exp: -0.00143

- Drop Ratio: 49.48%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
