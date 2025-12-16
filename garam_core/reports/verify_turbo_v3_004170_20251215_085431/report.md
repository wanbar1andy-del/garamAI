# Turbo V3 Verified Result (004170)

## Meta

- Run ID: `verify_turbo_v3_004170_20251215_085431`
- Timestamp (UTC): `2025-12-15T08:54:31Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `004170` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2841, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1870438.4030678854

## Key Points

- Total Return: -98.13%
- Max Drawdown: -98.21%
- Trades: 2841
- Final Equity: 1,870,438 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1420

- Win Rate: 29.23%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00030

- **Expectancy (Net)**: **-0.00250**

- Net PnL Total: -3.55013

- SQN Score: -14.54271


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 323 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 129 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2030 | 23 | 39.13% | **-0.00332** |  |
| CHOP_LOWVOL | 90936 | 1359 | 28.55% | **-0.00258** |  |
| PANIC | 1671 | 38 | 47.37% | **0.00090** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00240

- Last 20% Median Exp: -0.00248

- Drop Ratio: -3.23%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
