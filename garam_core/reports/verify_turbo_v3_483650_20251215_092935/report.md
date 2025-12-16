# Turbo V3 Verified Result (483650)

## Meta

- Run ID: `verify_turbo_v3_483650_20251215_092935`
- Timestamp (UTC): `2025-12-15T09:29:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `483650` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=1366, win_rate=0.00%, pnl=None, mdd=0.00%, equity=13009069.622677622

## Key Points

- Total Return: -86.99%
- Max Drawdown: -89.42%
- Trades: 1366
- Final Equity: 13,009,070 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 683

- Win Rate: 31.19%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00035

- **Expectancy (Net)**: **-0.00245**

- Net PnL Total: -1.67340

- SQN Score: -5.34133


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 119 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 392 | 1 | 0.00% | **-0.00735** |  |
| CHOP_HIGHVOL | 7171 | 78 | 28.21% | **-0.00169** |  |
| CHOP_LOWVOL | 44595 | 591 | 31.30% | **-0.00260** |  |
| PANIC | 878 | 13 | 46.15% | **0.00019** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00296

- Last 20% Median Exp: -0.00298

- Drop Ratio: -0.75%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
