# Turbo V3 Verified Result (078600)

## Meta

- Run ID: `verify_turbo_v3_078600_20251215_094701`
- Timestamp (UTC): `2025-12-15T09:47:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `078600` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2600, win_rate=0.00%, pnl=None, mdd=0.00%, equity=832447.4325099912

## Key Points

- Total Return: -99.17%
- Max Drawdown: -99.21%
- Trades: 2600
- Final Equity: 832,447 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1300

- Win Rate: 24.85%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00048

- **Expectancy (Net)**: **-0.00328**

- Net PnL Total: -4.26738

- SQN Score: -15.58033


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 182 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 155 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2335 | 23 | 43.48% | **-0.00478** |  |
| CHOP_LOWVOL | 91203 | 1257 | 24.26% | **-0.00326** |  |
| PANIC | 1233 | 20 | 40.00% | **-0.00282** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00328

- Last 20% Median Exp: -0.00301

- Drop Ratio: 8.39%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
