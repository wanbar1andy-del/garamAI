# Turbo V3 Verified Result (026960)

## Meta

- Run ID: `verify_turbo_v3_026960_20251215_055527`
- Timestamp (UTC): `2025-12-15T05:55:27Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `026960` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2984, win_rate=0.00%, pnl=None, mdd=0.00%, equity=813924.553888528

## Key Points

- Total Return: -99.19%
- Max Drawdown: -99.23%
- Trades: 2984
- Final Equity: 813,925 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1492

- Win Rate: 24.87%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00029

- **Expectancy (Net)**: **-0.00309**

- Net PnL Total: -4.60408

- SQN Score: -22.74779


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 44 | 1 | 100.00% | **0.01872** |  |
| TREND_DOWN | 24 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1127 | 8 | 25.00% | **-0.00696** |  |
| CHOP_LOWVOL | 89155 | 1459 | 24.95% | **-0.00303** |  |
| PANIC | 1148 | 24 | 16.67% | **-0.00606** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00311

- Last 20% Median Exp: -0.00312

- Drop Ratio: -0.35%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
