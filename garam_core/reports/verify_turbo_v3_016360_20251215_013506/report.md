# Turbo V3 Verified Result (016360)

## Meta

- Run ID: `verify_turbo_v3_016360_20251215_013506`
- Timestamp (UTC): `2025-12-15T01:35:06Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `016360` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3062, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1289841.44375976

## Key Points

- Total Return: -98.71%
- Max Drawdown: -98.71%
- Trades: 3062
- Final Equity: 1,289,841 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1531

- Win Rate: 30.37%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00029

- **Expectancy (Net)**: **-0.00251**

- Net PnL Total: -3.83986

- SQN Score: -15.99363


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 78 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 120 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 302 | 1 | 0.00% | **-0.00667** |  |
| CHOP_LOWVOL | 94543 | 1514 | 30.38% | **-0.00250** |  |
| PANIC | 829 | 16 | 31.25% | **-0.00299** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00264

- Last 20% Median Exp: -0.00224

- Drop Ratio: 15.10%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
