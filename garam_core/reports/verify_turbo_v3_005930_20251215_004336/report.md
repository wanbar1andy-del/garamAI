# Turbo V3 Verified Result (005930)

## Meta

- Run ID: `verify_turbo_v3_005930_20251215_004336`
- Timestamp (UTC): `2025-12-15T00:43:36Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005930` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3041, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1105781.9591268986

## Key Points

- Total Return: -98.89%
- Max Drawdown: -98.91%
- Trades: 3041
- Final Equity: 1,105,782 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1520

- Win Rate: 27.37%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00009

- **Expectancy (Net)**: **-0.00271**

- Net PnL Total: -4.11979

- SQN Score: -20.72425


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 285 | 3 | 0.00% | **-0.00746** |  |
| TREND_DOWN | 210 | 1 | 0.00% | **-0.00381** |  |
| CHOP_HIGHVOL | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94626 | 1508 | 27.39% | **-0.00270** |  |
| PANIC | 694 | 8 | 37.50% | **-0.00289** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00291

- Last 20% Median Exp: -0.00208

- Drop Ratio: 28.46%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
