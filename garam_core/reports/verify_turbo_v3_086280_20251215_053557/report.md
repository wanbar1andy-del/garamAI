# Turbo V3 Verified Result (086280)

## Meta

- Run ID: `verify_turbo_v3_086280_20251215_053557`
- Timestamp (UTC): `2025-12-15T05:35:57Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `086280` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2495, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2764691.112886809

## Key Points

- Total Return: -97.24%
- Max Drawdown: -97.29%
- Trades: 2495
- Final Equity: 2,764,691 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1247

- Win Rate: 30.95%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00033

- **Expectancy (Net)**: **-0.00247**

- Net PnL Total: -3.08414

- SQN Score: -12.10814


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 218 | 3 | 66.67% | **0.01017** |  |
| TREND_DOWN | 318 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 565 | 2 | 50.00% | **0.00760** |  |
| CHOP_LOWVOL | 93313 | 1219 | 30.43% | **-0.00254** |  |
| PANIC | 1450 | 23 | 52.17% | **-0.00142** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00233

- Last 20% Median Exp: -0.00273

- Drop Ratio: -17.16%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
