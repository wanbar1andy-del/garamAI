# Turbo V3 Verified Result (007340)

## Meta

- Run ID: `verify_turbo_v3_007340_20251215_095719`
- Timestamp (UTC): `2025-12-15T09:57:19Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `007340` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3114, win_rate=0.00%, pnl=None, mdd=0.00%, equity=578430.9284458744

## Key Points

- Total Return: -99.42%
- Max Drawdown: -99.42%
- Trades: 3114
- Final Equity: 578,431 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1557

- Win Rate: 24.66%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00021

- **Expectancy (Net)**: **-0.00301**

- Net PnL Total: -4.69129

- SQN Score: -16.12622


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 24 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6424 | 92 | 26.09% | **-0.00383** |  |
| CHOP_LOWVOL | 84708 | 1437 | 24.29% | **-0.00300** |  |
| PANIC | 1177 | 28 | 39.29% | **-0.00109** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00312

- Last 20% Median Exp: -0.00317

- Drop Ratio: -1.57%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
