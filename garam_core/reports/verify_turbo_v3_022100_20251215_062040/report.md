# Turbo V3 Verified Result (022100)

## Meta

- Run ID: `verify_turbo_v3_022100_20251215_062040`
- Timestamp (UTC): `2025-12-15T06:20:40Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `022100` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2673, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1298721.9932866753

## Key Points

- Total Return: -98.70%
- Max Drawdown: -98.78%
- Trades: 2673
- Final Equity: 1,298,722 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1336

- Win Rate: 23.88%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00010

- **Expectancy (Net)**: **-0.00290**

- Net PnL Total: -3.87906

- SQN Score: -10.00428


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 135 | 2 | 50.00% | **0.10932** |  |
| TREND_DOWN | 204 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6725 | 59 | 23.73% | **-0.00437** |  |
| CHOP_LOWVOL | 87338 | 1253 | 23.54% | **-0.00309** |  |
| PANIC | 953 | 22 | 40.91% | **0.00117** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00291

- Last 20% Median Exp: -0.00309

- Drop Ratio: -6.26%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
