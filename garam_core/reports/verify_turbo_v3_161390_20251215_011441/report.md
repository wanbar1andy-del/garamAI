# Turbo V3 Verified Result (161390)

## Meta

- Run ID: `verify_turbo_v3_161390_20251215_011441`
- Timestamp (UTC): `2025-12-15T01:14:41Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `161390` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3053, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1126628.3837862338

## Key Points

- Total Return: -98.87%
- Max Drawdown: -98.92%
- Trades: 3053
- Final Equity: 1,126,628 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1526

- Win Rate: 30.21%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00023

- **Expectancy (Net)**: **-0.00257**

- Net PnL Total: -3.92150

- SQN Score: -12.71954


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 122 | 1 | 0.00% | **-0.00519** |  |
| TREND_DOWN | 140 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 966 | 9 | 44.44% | **-0.00250** |  |
| CHOP_LOWVOL | 93507 | 1495 | 30.10% | **-0.00256** |  |
| PANIC | 998 | 21 | 33.33% | **-0.00342** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00273

- Last 20% Median Exp: -0.00190

- Drop Ratio: 30.24%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
