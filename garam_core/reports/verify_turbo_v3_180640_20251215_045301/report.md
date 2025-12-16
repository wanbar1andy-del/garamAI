# Turbo V3 Verified Result (180640)

## Meta

- Run ID: `verify_turbo_v3_180640_20251215_045301`
- Timestamp (UTC): `2025-12-15T04:53:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `180640` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2626, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1953385.2523399214

## Key Points

- Total Return: -98.05%
- Max Drawdown: -98.22%
- Trades: 2626
- Final Equity: 1,953,385 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1313

- Win Rate: 28.03%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00010

- **Expectancy (Net)**: **-0.00270**

- Net PnL Total: -3.54031

- SQN Score: -7.22554


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 274 | 1 | 0.00% | **-0.06061** |  |
| TREND_DOWN | 73 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3842 | 44 | 25.00% | **0.00165** |  |
| CHOP_LOWVOL | 86073 | 1236 | 27.75% | **-0.00275** |  |
| PANIC | 1578 | 32 | 43.75% | **-0.00492** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00292

- Last 20% Median Exp: -0.00248

- Drop Ratio: 15.17%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
