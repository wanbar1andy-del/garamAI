# Turbo V3 Verified Result (439260)

## Meta

- Run ID: `verify_turbo_v3_439260_20251215_043920`
- Timestamp (UTC): `2025-12-15T04:39:20Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `439260` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=891, win_rate=0.00%, pnl=None, mdd=0.00%, equity=22630269.183083016

## Key Points

- Total Return: -77.37%
- Max Drawdown: -81.75%
- Trades: 891
- Final Equity: 22,630,269 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 445

- Win Rate: 22.92%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00017

- **Expectancy (Net)**: **-0.00297**

- Net PnL Total: -1.32347

- SQN Score: -5.54015


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 40 | 1 | 0.00% | **-0.00945** |  |
| TREND_DOWN | 75 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3730 | 34 | 32.35% | **-0.00059** |  |
| CHOP_LOWVOL | 30135 | 400 | 21.50% | **-0.00322** |  |
| PANIC | 463 | 10 | 50.00% | **-0.00077** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00372

- Last 20% Median Exp: -0.00278

- Drop Ratio: 25.14%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
