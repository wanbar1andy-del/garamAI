# Turbo V3 Verified Result (139480)

## Meta

- Run ID: `verify_turbo_v3_139480_20251215_093702`
- Timestamp (UTC): `2025-12-15T09:37:02Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `139480` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2888, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1438312.2677516013

## Key Points

- Total Return: -98.56%
- Max Drawdown: -98.64%
- Trades: 2888
- Final Equity: 1,438,312 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1444

- Win Rate: 25.62%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00011

- **Expectancy (Net)**: **-0.00269**

- Net PnL Total: -3.88740

- SQN Score: -15.09940


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 151 | 1 | 100.00% | **0.03729** |  |
| TREND_DOWN | 110 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 783 | 4 | 50.00% | **-0.00065** |  |
| CHOP_LOWVOL | 93694 | 1415 | 25.16% | **-0.00283** |  |
| PANIC | 1084 | 24 | 45.83% | **0.00361** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00280

- Last 20% Median Exp: -0.00294

- Drop Ratio: -4.89%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
