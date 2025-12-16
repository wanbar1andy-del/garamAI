# Turbo V3 Verified Result (457190)

## Meta

- Run ID: `verify_turbo_v3_457190_20251215_074518`
- Timestamp (UTC): `2025-12-15T07:45:18Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `457190` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2516, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1452582.2646205216

## Key Points

- Total Return: -98.55%
- Max Drawdown: -98.59%
- Trades: 2516
- Final Equity: 1,452,582 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1258

- Win Rate: 26.15%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00012

- **Expectancy (Net)**: **-0.00292**

- Net PnL Total: -3.67827

- SQN Score: -9.49198


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 112 | 4 | 0.00% | **-0.02521** |  |
| TREND_DOWN | 180 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 8974 | 96 | 30.21% | **-0.00469** |  |
| CHOP_LOWVOL | 84643 | 1125 | 25.42% | **-0.00271** |  |
| PANIC | 1322 | 33 | 42.42% | **-0.00253** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00288

- Last 20% Median Exp: -0.00337

- Drop Ratio: -17.08%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
