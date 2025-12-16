# Turbo V3 Verified Result (005490)

## Meta

- Run ID: `verify_turbo_v3_005490_20251215_004344`
- Timestamp (UTC): `2025-12-15T00:43:44Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005490` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2963, win_rate=0.00%, pnl=None, mdd=0.00%, equity=757459.157749086

## Key Points

- Total Return: -99.24%
- Max Drawdown: -99.24%
- Trades: 2963
- Final Equity: 757,459 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1481

- Win Rate: 25.39%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00017

- **Expectancy (Net)**: **-0.00297**

- Net PnL Total: -4.39536

- SQN Score: -16.96759


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 37 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 11 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 397 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94677 | 1471 | 25.15% | **-0.00301** |  |
| PANIC | 689 | 10 | 60.00% | **0.00261** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00292

- Last 20% Median Exp: -0.00265

- Drop Ratio: 9.20%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
