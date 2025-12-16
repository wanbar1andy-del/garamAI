# Turbo V3 Verified Result (086790)

## Meta

- Run ID: `verify_turbo_v3_086790_20251215_025236`
- Timestamp (UTC): `2025-12-15T02:52:36Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `086790` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3208, win_rate=0.00%, pnl=None, mdd=0.00%, equity=676122.5398985556

## Key Points

- Total Return: -99.32%
- Max Drawdown: -99.33%
- Trades: 3208
- Final Equity: 676,123 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1604

- Win Rate: 27.68%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00005

- **Expectancy (Net)**: **-0.00285**

- Net PnL Total: -4.56693

- SQN Score: -21.38093


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 166 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 162 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 212 | 1 | 100.00% | **0.00809** |  |
| CHOP_LOWVOL | 94504 | 1583 | 27.61% | **-0.00282** |  |
| PANIC | 835 | 20 | 30.00% | **-0.00530** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00289

- Last 20% Median Exp: -0.00263

- Drop Ratio: 9.15%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
