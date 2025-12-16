# Turbo V3 Verified Result (108490)

## Meta

- Run ID: `verify_turbo_v3_108490_20251215_053142`
- Timestamp (UTC): `2025-12-15T05:31:42Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `108490` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2443, win_rate=0.00%, pnl=None, mdd=0.00%, equity=6473176.552385269

## Key Points

- Total Return: -93.53%
- Max Drawdown: -94.15%
- Trades: 2443
- Final Equity: 6,473,177 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1221

- Win Rate: 26.13%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00097

- **Expectancy (Net)**: **-0.00183**

- Net PnL Total: -2.23715

- SQN Score: -3.10820


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 469 | 4 | 25.00% | **0.00161** |  |
| TREND_DOWN | 88 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 22680 | 227 | 30.40% | **0.00010** |  |
| CHOP_LOWVOL | 70522 | 954 | 24.42% | **-0.00234** |  |
| PANIC | 1603 | 36 | 44.44% | **-0.00100** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00182

- Last 20% Median Exp: -0.00034

- Drop Ratio: 81.10%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
