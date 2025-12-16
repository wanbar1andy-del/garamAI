# Turbo V3 Verified Result (138040)

## Meta

- Run ID: `verify_turbo_v3_138040_20251215_050943`
- Timestamp (UTC): `2025-12-15T05:09:43Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `138040` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2863, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1286130.6788089697

## Key Points

- Total Return: -98.71%
- Max Drawdown: -98.72%
- Trades: 2863
- Final Equity: 1,286,131 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1431

- Win Rate: 28.23%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00007

- **Expectancy (Net)**: **-0.00273**

- Net PnL Total: -3.90258

- SQN Score: -20.50782


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 128 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 187 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 48 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94370 | 1403 | 28.15% | **-0.00271** |  |
| PANIC | 1111 | 28 | 32.14% | **-0.00367** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00276

- Last 20% Median Exp: -0.00233

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
