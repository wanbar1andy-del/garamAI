# Turbo V3 Verified Result (009830)

## Meta

- Run ID: `verify_turbo_v3_009830_20251215_034103`
- Timestamp (UTC): `2025-12-15T03:41:03Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `009830` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2802, win_rate=0.00%, pnl=None, mdd=0.00%, equity=993365.8632073937

## Key Points

- Total Return: -99.01%
- Max Drawdown: -99.01%
- Trades: 2802
- Final Equity: 993,366 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1401

- Win Rate: 24.98%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00016

- **Expectancy (Net)**: **-0.00296**

- Net PnL Total: -4.15049

- SQN Score: -9.75594


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 306 | 5 | 100.00% | **0.02353** |  |
| TREND_DOWN | 281 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6668 | 63 | 25.40% | **-0.00230** |  |
| CHOP_LOWVOL | 87654 | 1304 | 24.69% | **-0.00299** |  |
| PANIC | 975 | 29 | 24.14% | **-0.00760** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00294

- Last 20% Median Exp: -0.00344

- Drop Ratio: -16.86%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
