# Turbo V3 Verified Result (466100)

## Meta

- Run ID: `verify_turbo_v3_466100_20251215_094116`
- Timestamp (UTC): `2025-12-15T09:41:16Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `466100` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2287, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4257857.219380572

## Key Points

- Total Return: -95.74%
- Max Drawdown: -96.51%
- Trades: 2287
- Final Equity: 4,257,857 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1143

- Win Rate: 27.03%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00045

- **Expectancy (Net)**: **-0.00235**

- Net PnL Total: -2.68907

- SQN Score: -4.31974


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 300 | 1 | 100.00% | **0.00798** |  |
| TREND_DOWN | 415 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 19722 | 203 | 29.56% | **-0.00111** |  |
| CHOP_LOWVOL | 73488 | 900 | 26.22% | **-0.00251** |  |
| PANIC | 1611 | 39 | 30.77% | **-0.00546** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00320

- Last 20% Median Exp: -0.00206

- Drop Ratio: 35.58%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
