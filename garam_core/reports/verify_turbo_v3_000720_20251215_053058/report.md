# Turbo V3 Verified Result (000720)

## Meta

- Run ID: `verify_turbo_v3_000720_20251215_053058`
- Timestamp (UTC): `2025-12-15T05:30:58Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000720` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2785, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2861605.6639929656

## Key Points

- Total Return: -97.14%
- Max Drawdown: -97.14%
- Trades: 2785
- Final Equity: 2,861,606 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1392

- Win Rate: 28.52%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00044

- **Expectancy (Net)**: **-0.00236**

- Net PnL Total: -3.28731

- SQN Score: -8.71358


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 180 | 1 | 0.00% | **-0.00701** |  |
| TREND_DOWN | 225 | 1 | 0.00% | **-0.00452** |  |
| CHOP_HIGHVOL | 4870 | 55 | 25.45% | **-0.00233** |  |
| CHOP_LOWVOL | 89650 | 1312 | 28.66% | **-0.00232** |  |
| PANIC | 949 | 23 | 30.43% | **-0.00432** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00209

- Last 20% Median Exp: -0.00225

- Drop Ratio: -7.79%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
