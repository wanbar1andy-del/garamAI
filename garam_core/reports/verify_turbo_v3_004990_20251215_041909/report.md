# Turbo V3 Verified Result (004990)

## Meta

- Run ID: `verify_turbo_v3_004990_20251215_041909`
- Timestamp (UTC): `2025-12-15T04:19:09Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `004990` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3343, win_rate=0.00%, pnl=None, mdd=0.00%, equity=603846.5690102481

## Key Points

- Total Return: -99.40%
- Max Drawdown: -99.42%
- Trades: 3343
- Final Equity: 603,847 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1671

- Win Rate: 25.37%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00003

- **Expectancy (Net)**: **-0.00277**

- Net PnL Total: -4.63187

- SQN Score: -18.33256


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 81 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 33 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2244 | 24 | 25.00% | **0.00035** |  |
| CHOP_LOWVOL | 90660 | 1627 | 25.26% | **-0.00283** |  |
| PANIC | 882 | 20 | 35.00% | **-0.00180** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00295

- Last 20% Median Exp: -0.00296

- Drop Ratio: -0.37%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
