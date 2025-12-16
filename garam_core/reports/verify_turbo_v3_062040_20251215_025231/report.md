# Turbo V3 Verified Result (062040)

## Meta

- Run ID: `verify_turbo_v3_062040_20251215_025231`
- Timestamp (UTC): `2025-12-15T02:52:31Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `062040` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2557, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1953191.5193053298

## Key Points

- Total Return: -98.05%
- Max Drawdown: -98.23%
- Trades: 2557
- Final Equity: 1,953,192 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1278

- Win Rate: 26.76%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00008

- **Expectancy (Net)**: **-0.00288**

- Net PnL Total: -3.67470

- SQN Score: -9.51160


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 255 | 2 | 50.00% | **0.01083** |  |
| TREND_DOWN | 161 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6781 | 62 | 20.97% | **-0.00636** |  |
| CHOP_LOWVOL | 87234 | 1188 | 26.94% | **-0.00265** |  |
| PANIC | 1428 | 26 | 30.77% | **-0.00579** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00305

- Last 20% Median Exp: -0.00296

- Drop Ratio: 2.74%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
