# Turbo V3 Verified Result (004020)

## Meta

- Run ID: `verify_turbo_v3_004020_20251215_063550`
- Timestamp (UTC): `2025-12-15T06:35:50Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `004020` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3133, win_rate=0.00%, pnl=None, mdd=0.00%, equity=821541.9191638161

## Key Points

- Total Return: -99.18%
- Max Drawdown: -99.18%
- Trades: 3133
- Final Equity: 821,542 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1566

- Win Rate: 25.48%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00001

- **Expectancy (Net)**: **-0.00279**

- Net PnL Total: -4.37011

- SQN Score: -13.91687


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 90 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 7 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3908 | 40 | 30.00% | **-0.00364** |  |
| CHOP_LOWVOL | 91076 | 1506 | 25.10% | **-0.00280** |  |
| PANIC | 786 | 20 | 45.00% | **-0.00043** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00274

- Last 20% Median Exp: -0.00291

- Drop Ratio: -6.43%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
