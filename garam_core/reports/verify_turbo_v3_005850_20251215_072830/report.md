# Turbo V3 Verified Result (005850)

## Meta

- Run ID: `verify_turbo_v3_005850_20251215_072830`
- Timestamp (UTC): `2025-12-15T07:28:30Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005850` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2945, win_rate=0.00%, pnl=None, mdd=0.00%, equity=961170.7783361649

## Key Points

- Total Return: -99.04%
- Max Drawdown: -99.05%
- Trades: 2945
- Final Equity: 961,171 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1472

- Win Rate: 28.46%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00001

- **Expectancy (Net)**: **-0.00279**

- Net PnL Total: -4.10117

- SQN Score: -15.62961


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 109 | 4 | 25.00% | **-0.00202** |  |
| TREND_DOWN | 1 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2559 | 17 | 47.06% | **-0.00043** |  |
| CHOP_LOWVOL | 91423 | 1433 | 28.19% | **-0.00279** |  |
| PANIC | 1021 | 18 | 33.33% | **-0.00475** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00280

- Last 20% Median Exp: -0.00355

- Drop Ratio: -26.79%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
