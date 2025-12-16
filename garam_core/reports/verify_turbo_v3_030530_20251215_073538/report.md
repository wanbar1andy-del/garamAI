# Turbo V3 Verified Result (030530)

## Meta

- Run ID: `verify_turbo_v3_030530_20251215_073538`
- Timestamp (UTC): `2025-12-15T07:35:38Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `030530` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2445, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4532386.374430403

## Key Points

- Total Return: -95.47%
- Max Drawdown: -96.05%
- Trades: 2445
- Final Equity: 4,532,386 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1222

- Win Rate: 26.92%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00034

- **Expectancy (Net)**: **-0.00246**

- Net PnL Total: -3.00324

- SQN Score: -4.80639


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 452 | 7 | 57.14% | **0.06209** |  |
| TREND_DOWN | 30 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 22612 | 225 | 26.67% | **-0.00327** |  |
| CHOP_LOWVOL | 68825 | 952 | 26.26% | **-0.00266** |  |
| PANIC | 1407 | 38 | 39.47% | **-0.00449** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00239

- Last 20% Median Exp: -0.00267

- Drop Ratio: -11.81%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
