# Turbo V3 Verified Result (128940)

## Meta

- Run ID: `verify_turbo_v3_128940_20251215_074343`
- Timestamp (UTC): `2025-12-15T07:43:43Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `128940` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3215, win_rate=0.00%, pnl=None, mdd=0.00%, equity=687900.7477346003

## Key Points

- Total Return: -99.31%
- Max Drawdown: -99.32%
- Trades: 3215
- Final Equity: 687,901 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1607

- Win Rate: 26.57%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00005

- **Expectancy (Net)**: **-0.00285**

- Net PnL Total: -4.58542

- SQN Score: -15.54577


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 152 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 28 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2112 | 23 | 26.09% | **-0.00161** |  |
| CHOP_LOWVOL | 92436 | 1559 | 26.49% | **-0.00284** |  |
| PANIC | 911 | 25 | 32.00% | **-0.00487** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00306

- Last 20% Median Exp: -0.00235

- Drop Ratio: 23.06%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
