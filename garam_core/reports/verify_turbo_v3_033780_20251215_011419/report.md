# Turbo V3 Verified Result (033780)

## Meta

- Run ID: `verify_turbo_v3_033780_20251215_011419`
- Timestamp (UTC): `2025-12-15T01:14:19Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `033780` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2840, win_rate=0.00%, pnl=None, mdd=0.00%, equity=873646.4185932359

## Key Points

- Total Return: -99.13%
- Max Drawdown: -99.13%
- Trades: 2840
- Final Equity: 873,646 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1420

- Win Rate: 29.37%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00028

- **Expectancy (Net)**: **-0.00308**

- Net PnL Total: -4.37793

- SQN Score: -28.67180


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 51 | 1 | 0.00% | **-0.02540** |  |
| TREND_DOWN | 7 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 242 | 1 | 100.00% | **0.00066** |  |
| CHOP_LOWVOL | 94147 | 1384 | 29.26% | **-0.00307** |  |
| PANIC | 1314 | 34 | 32.35% | **-0.00325** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00315

- Last 20% Median Exp: -0.00295

- Drop Ratio: 6.47%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
