# Turbo V3 Verified Result (097230)

## Meta

- Run ID: `verify_turbo_v3_097230_20251215_073549`
- Timestamp (UTC): `2025-12-15T07:35:49Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `097230` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2473, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2782239.9686594456

## Key Points

- Total Return: -97.22%
- Max Drawdown: -97.66%
- Trades: 2473
- Final Equity: 2,782,240 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1236

- Win Rate: 25.81%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00041

- **Expectancy (Net)**: **-0.00239**

- Net PnL Total: -2.95728

- SQN Score: -3.92522


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 173 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 86 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 25865 | 262 | 27.48% | **-0.00368** |  |
| CHOP_LOWVOL | 66176 | 943 | 24.60% | **-0.00287** |  |
| PANIC | 1492 | 31 | 48.39% | **0.02294** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00287

- Last 20% Median Exp: -0.00343

- Drop Ratio: -19.46%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
