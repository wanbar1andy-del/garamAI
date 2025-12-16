# Turbo V3 Verified Result (055550)

## Meta

- Run ID: `verify_turbo_v3_055550_20251215_010428`
- Timestamp (UTC): `2025-12-15T01:04:28Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `055550` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3189, win_rate=0.00%, pnl=None, mdd=0.00%, equity=700724.798389482

## Key Points

- Total Return: -99.30%
- Max Drawdown: -99.31%
- Trades: 3189
- Final Equity: 700,725 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1594

- Win Rate: 25.41%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00007

- **Expectancy (Net)**: **-0.00287**

- Net PnL Total: -4.57574

- SQN Score: -24.24879


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 42 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 5 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 305 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94619 | 1575 | 25.14% | **-0.00289** |  |
| PANIC | 831 | 19 | 47.37% | **-0.00115** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00291

- Last 20% Median Exp: -0.00272

- Drop Ratio: 6.50%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
