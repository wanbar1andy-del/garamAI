# Turbo V3 Verified Result (051600)

## Meta

- Run ID: `verify_turbo_v3_051600_20251215_085140`
- Timestamp (UTC): `2025-12-15T08:51:40Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `051600` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3128, win_rate=0.00%, pnl=None, mdd=0.00%, equity=708397.3076881926

## Key Points

- Total Return: -99.29%
- Max Drawdown: -99.29%
- Trades: 3128
- Final Equity: 708,397 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1564

- Win Rate: 26.34%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00008

- **Expectancy (Net)**: **-0.00288**

- Net PnL Total: -4.50735

- SQN Score: -16.62210


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 265 | 1 | 100.00% | **0.05898** |  |
| TREND_DOWN | 184 | 1 | 0.00% | **-0.00903** |  |
| CHOP_HIGHVOL | 2408 | 23 | 17.39% | **-0.00849** |  |
| CHOP_LOWVOL | 91838 | 1517 | 26.43% | **-0.00280** |  |
| PANIC | 965 | 22 | 27.27% | **-0.00504** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00290

- Last 20% Median Exp: -0.00298

- Drop Ratio: -2.68%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
