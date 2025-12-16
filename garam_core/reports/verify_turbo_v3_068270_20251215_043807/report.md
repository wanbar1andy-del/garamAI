# Turbo V3 Verified Result (068270)

## Meta

- Run ID: `verify_turbo_v3_068270_20251215_043807`
- Timestamp (UTC): `2025-12-15T04:38:07Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `068270` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2535, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1900869.2467131703

## Key Points

- Total Return: -98.10%
- Max Drawdown: -98.12%
- Trades: 2535
- Final Equity: 1,900,869 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1267

- Win Rate: 26.36%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00004

- **Expectancy (Net)**: **-0.00284**

- Net PnL Total: -3.59694

- SQN Score: -19.80340


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 325 | 3 | 33.33% | **-0.01351** |  |
| TREND_DOWN | 391 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 65 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 93774 | 1226 | 25.86% | **-0.00282** |  |
| PANIC | 1342 | 38 | 42.11% | **-0.00263** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00291

- Last 20% Median Exp: -0.00260

- Drop Ratio: 10.43%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
