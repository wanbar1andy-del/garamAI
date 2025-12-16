# Turbo V3 Verified Result (001450)

## Meta

- Run ID: `verify_turbo_v3_001450_20251215_084916`
- Timestamp (UTC): `2025-12-15T08:49:16Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `001450` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3492, win_rate=0.00%, pnl=None, mdd=0.00%, equity=457941.02937478403

## Key Points

- Total Return: -99.54%
- Max Drawdown: -99.54%
- Trades: 3492
- Final Equity: 457,941 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1746

- Win Rate: 23.94%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00008

- **Expectancy (Net)**: **-0.00288**

- Net PnL Total: -5.03562

- SQN Score: -23.22670


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 58 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 46 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 861 | 6 | 33.33% | **-0.00480** |  |
| CHOP_LOWVOL | 94081 | 1729 | 23.83% | **-0.00288** |  |
| PANIC | 699 | 11 | 36.36% | **-0.00317** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00288

- Last 20% Median Exp: -0.00291

- Drop Ratio: -1.05%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
