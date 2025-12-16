# Turbo V3 Verified Result (290650)

## Meta

- Run ID: `verify_turbo_v3_290650_20251215_084500`
- Timestamp (UTC): `2025-12-15T08:45:00Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `290650` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2478, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1823728.7588062636

## Key Points

- Total Return: -98.18%
- Max Drawdown: -98.24%
- Trades: 2478
- Final Equity: 1,823,729 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1239

- Win Rate: 27.93%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00005

- **Expectancy (Net)**: **-0.00275**

- Net PnL Total: -3.41203

- SQN Score: -7.03690


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 170 | 2 | 0.00% | **-0.03650** |  |
| TREND_DOWN | 29 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 13249 | 133 | 27.07% | **-0.00279** |  |
| CHOP_LOWVOL | 74667 | 1074 | 28.12% | **-0.00249** |  |
| PANIC | 1357 | 30 | 26.67% | **-0.00965** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00269

- Last 20% Median Exp: -0.00402

- Drop Ratio: -49.42%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
