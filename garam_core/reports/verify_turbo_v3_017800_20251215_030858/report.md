# Turbo V3 Verified Result (017800)

## Meta

- Run ID: `verify_turbo_v3_017800_20251215_030858`
- Timestamp (UTC): `2025-12-15T03:08:58Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `017800` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3164, win_rate=0.00%, pnl=None, mdd=0.00%, equity=643767.3594857474

## Key Points

- Total Return: -99.36%
- Max Drawdown: -99.36%
- Trades: 3164
- Final Equity: 643,767 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1582

- Win Rate: 27.56%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00009

- **Expectancy (Net)**: **-0.00289**

- Net PnL Total: -4.56572

- SQN Score: -18.10220


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 45 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 1 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4687 | 43 | 44.19% | **-0.00098** |  |
| CHOP_LOWVOL | 89964 | 1515 | 26.80% | **-0.00293** |  |
| PANIC | 1115 | 24 | 45.83% | **-0.00353** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00298

- Last 20% Median Exp: -0.00307

- Drop Ratio: -3.18%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
