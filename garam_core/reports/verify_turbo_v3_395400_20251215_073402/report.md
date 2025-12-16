# Turbo V3 Verified Result (395400)

## Meta

- Run ID: `verify_turbo_v3_395400_20251215_073402`
- Timestamp (UTC): `2025-12-15T07:34:02Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `395400` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3761, win_rate=0.00%, pnl=None, mdd=0.00%, equity=214929.45245683554

## Key Points

- Total Return: -99.79%
- Max Drawdown: -99.79%
- Trades: 3761
- Final Equity: 214,929 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1880

- Win Rate: 25.32%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00017

- **Expectancy (Net)**: **-0.00297**

- Net PnL Total: -5.57542

- SQN Score: -46.27319


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 9 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 36 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 290 | 13 | 15.38% | **-0.00390** |  |
| CHOP_LOWVOL | 91902 | 1844 | 25.11% | **-0.00296** |  |
| PANIC | 1261 | 23 | 47.83% | **-0.00252** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00293

- Last 20% Median Exp: -0.00312

- Drop Ratio: -6.58%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
