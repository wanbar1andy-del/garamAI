# Turbo V3 Verified Result (005930)

## Meta

- Run ID: `verify_turbo_v3_005930_20251214_234336`
- Timestamp (UTC): `2025-12-14T23:43:36Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005930` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=122, win_rate=0.00%, pnl=None, mdd=0.00%, equity=85643688.12429269

## Key Points

- Total Return: -14.36%
- Max Drawdown: -16.00%
- Trades: 122
- Final Equity: 85,643,688 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 61

- Win Rate: 26.23%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00055

- **Expectancy (Net)**: **-0.00225**

- Net PnL Total: -0.13715

- SQN Score: -3.61547


### Collapse Tags (Automated)

- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 285 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 210 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94626 | 61 | 26.23% | **-0.00225** |  |
| PANIC | 694 | 0 | 0.00% | **0.00000** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: 0.00000

- Last 20% Median Exp: 0.00000

- Drop Ratio: 0.00%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
