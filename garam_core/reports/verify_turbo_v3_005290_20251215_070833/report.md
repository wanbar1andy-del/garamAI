# Turbo V3 Verified Result (005290)

## Meta

- Run ID: `verify_turbo_v3_005290_20251215_070833`
- Timestamp (UTC): `2025-12-15T07:08:33Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005290` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2814, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1444732.663008718

## Key Points

- Total Return: -98.56%
- Max Drawdown: -98.56%
- Trades: 2814
- Final Equity: 1,444,733 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1407

- Win Rate: 26.65%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00017

- **Expectancy (Net)**: **-0.00263**

- Net PnL Total: -3.70423

- SQN Score: -11.35165


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 89 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 254 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3872 | 28 | 35.71% | **0.00008** |  |
| CHOP_LOWVOL | 90585 | 1357 | 26.23% | **-0.00274** |  |
| PANIC | 888 | 22 | 40.91% | **0.00026** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00273

- Last 20% Median Exp: -0.00210

- Drop Ratio: 22.92%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
