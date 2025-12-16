# Turbo V3 Verified Result (139130)

## Meta

- Run ID: `verify_turbo_v3_139130_20251215_082239`
- Timestamp (UTC): `2025-12-15T08:22:39Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `139130` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3095, win_rate=0.00%, pnl=None, mdd=0.00%, equity=890682.5032546122

## Key Points

- Total Return: -99.11%
- Max Drawdown: -99.12%
- Trades: 3095
- Final Equity: 890,683 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1547

- Win Rate: 28.77%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00002

- **Expectancy (Net)**: **-0.00282**

- Net PnL Total: -4.36276

- SQN Score: -24.97704


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 35 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 184 | 1 | 0.00% | **-0.00605** |  |
| CHOP_HIGHVOL | 52 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 93833 | 1514 | 28.47% | **-0.00283** |  |
| PANIC | 1545 | 32 | 43.75% | **-0.00205** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00276

- Last 20% Median Exp: -0.00313

- Drop Ratio: -13.37%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
