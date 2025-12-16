# Turbo V3 Verified Result (298040)

## Meta

- Run ID: `verify_turbo_v3_298040_20251215_004330`
- Timestamp (UTC): `2025-12-15T00:43:30Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `298040` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2544, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3663368.6471206504

## Key Points

- Total Return: -96.34%
- Max Drawdown: -96.60%
- Trades: 2544
- Final Equity: 3,663,369 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1272

- Win Rate: 30.82%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00058

- **Expectancy (Net)**: **-0.00222**

- Net PnL Total: -2.82363

- SQN Score: -7.09048


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 411 | 5 | 40.00% | **-0.00237** |  |
| TREND_DOWN | 356 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4906 | 51 | 29.41% | **-0.00465** |  |
| CHOP_LOWVOL | 88768 | 1188 | 30.56% | **-0.00214** |  |
| PANIC | 1342 | 28 | 42.86% | **-0.00116** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00209

- Last 20% Median Exp: -0.00255

- Drop Ratio: -22.11%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
