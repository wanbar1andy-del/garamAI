# Turbo V3 Verified Result (383220)

## Meta

- Run ID: `verify_turbo_v3_383220_20251215_061409`
- Timestamp (UTC): `2025-12-15T06:14:09Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `383220` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3184, win_rate=0.00%, pnl=None, mdd=0.00%, equity=559672.7430315829

## Key Points

- Total Return: -99.44%
- Max Drawdown: -99.44%
- Trades: 3184
- Final Equity: 559,673 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1592

- Win Rate: 31.53%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00008

- **Expectancy (Net)**: **-0.00288**

- Net PnL Total: -4.58328

- SQN Score: -19.60921


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 108 | 1 | 0.00% | **-0.00660** |  |
| TREND_DOWN | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6331 | 86 | 44.19% | **-0.00045** |  |
| CHOP_LOWVOL | 87896 | 1489 | 30.62% | **-0.00301** |  |
| PANIC | 1130 | 16 | 50.00% | **-0.00356** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00289

- Last 20% Median Exp: -0.00278

- Drop Ratio: 3.99%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
