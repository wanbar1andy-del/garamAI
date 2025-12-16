# Turbo V3 Verified Result (031210)

## Meta

- Run ID: `verify_turbo_v3_031210_20251215_033636`
- Timestamp (UTC): `2025-12-15T03:36:36Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `031210` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2416, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2414415.57091947

## Key Points

- Total Return: -97.59%
- Max Drawdown: -97.79%
- Trades: 2416
- Final Equity: 2,414,416 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1208

- Win Rate: 29.14%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00001

- **Expectancy (Net)**: **-0.00281**

- Net PnL Total: -3.39650

- SQN Score: -14.35101


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 19 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 9 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2530 | 31 | 29.03% | **-0.00562** |  |
| CHOP_LOWVOL | 66707 | 1162 | 28.92% | **-0.00289** |  |
| PANIC | 832 | 15 | 46.67% | **0.00878** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00285

- Last 20% Median Exp: -0.00288

- Drop Ratio: -1.07%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
