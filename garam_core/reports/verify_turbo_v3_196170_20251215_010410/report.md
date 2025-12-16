# Turbo V3 Verified Result (196170)

## Meta

- Run ID: `verify_turbo_v3_196170_20251215_010410`
- Timestamp (UTC): `2025-12-15T01:04:10Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `196170` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2490, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2456458.1126573966

## Key Points

- Total Return: -97.54%
- Max Drawdown: -97.66%
- Trades: 2490
- Final Equity: 2,456,458 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1245

- Win Rate: 26.02%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00022

- **Expectancy (Net)**: **-0.00258**

- Net PnL Total: -3.21044

- SQN Score: -9.13448


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 151 | 2 | 50.00% | **0.00063** |  |
| TREND_DOWN | 57 | 1 | 100.00% | **0.00419** |  |
| CHOP_HIGHVOL | 3463 | 30 | 30.00% | **-0.00474** |  |
| CHOP_LOWVOL | 90930 | 1194 | 25.63% | **-0.00260** |  |
| PANIC | 1214 | 18 | 38.89% | **0.00164** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00249

- Last 20% Median Exp: -0.00315

- Drop Ratio: -26.58%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
