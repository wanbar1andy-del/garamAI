# Turbo V3 Verified Result (015760)

## Meta

- Run ID: `verify_turbo_v3_015760_20251215_013611`
- Timestamp (UTC): `2025-12-15T01:36:11Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `015760` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3182, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1197152.2415737736

## Key Points

- Total Return: -98.80%
- Max Drawdown: -98.80%
- Trades: 3182
- Final Equity: 1,197,152 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1591

- Win Rate: 27.28%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00029

- **Expectancy (Net)**: **-0.00251**

- Net PnL Total: -3.98841

- SQN Score: -13.86876


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 262 | 4 | 50.00% | **0.00341** |  |
| TREND_DOWN | 121 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2902 | 22 | 36.36% | **-0.00348** |  |
| CHOP_LOWVOL | 91769 | 1556 | 26.74% | **-0.00261** |  |
| PANIC | 837 | 9 | 88.89% | **0.01450** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00264

- Last 20% Median Exp: -0.00236

- Drop Ratio: 10.43%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
