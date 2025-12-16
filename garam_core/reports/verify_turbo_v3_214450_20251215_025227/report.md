# Turbo V3 Verified Result (214450)

## Meta

- Run ID: `verify_turbo_v3_214450_20251215_025227`
- Timestamp (UTC): `2025-12-15T02:52:27Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `214450` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2622, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2728200.0927883857

## Key Points

- Total Return: -97.27%
- Max Drawdown: -97.29%
- Trades: 2622
- Final Equity: 2,728,200 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1311

- Win Rate: 29.06%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00041

- **Expectancy (Net)**: **-0.00239**

- Net PnL Total: -3.13151

- SQN Score: -8.60052


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 26 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 119 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 9652 | 83 | 36.14% | **-0.00011** |  |
| CHOP_LOWVOL | 84833 | 1199 | 28.19% | **-0.00268** |  |
| PANIC | 1205 | 29 | 44.83% | **0.00326** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00274

- Last 20% Median Exp: -0.00178

- Drop Ratio: 34.86%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
