# Turbo V3 Verified Result (068760)

## Meta

- Run ID: `verify_turbo_v3_068760_20251215_063935`
- Timestamp (UTC): `2025-12-15T06:39:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `068760` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2905, win_rate=0.00%, pnl=None, mdd=0.00%, equity=890214.839235111

## Key Points

- Total Return: -99.11%
- Max Drawdown: -99.13%
- Trades: 2905
- Final Equity: 890,215 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1452

- Win Rate: 26.10%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00017

- **Expectancy (Net)**: **-0.00297**

- Net PnL Total: -4.30818

- SQN Score: -21.58362


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 44 | 2 | 0.00% | **-0.02334** |  |
| TREND_DOWN | 22 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1439 | 11 | 9.09% | **-0.00950** |  |
| CHOP_LOWVOL | 87189 | 1405 | 26.05% | **-0.00284** |  |
| PANIC | 1042 | 34 | 35.29% | **-0.00504** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00313

- Last 20% Median Exp: -0.00264

- Drop Ratio: 15.63%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
