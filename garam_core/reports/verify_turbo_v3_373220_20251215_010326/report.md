# Turbo V3 Verified Result (373220)

## Meta

- Run ID: `verify_turbo_v3_373220_20251215_010326`
- Timestamp (UTC): `2025-12-15T01:03:26Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `373220` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2739, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1407552.769280062

## Key Points

- Total Return: -98.59%
- Max Drawdown: -98.61%
- Trades: 2739
- Final Equity: 1,407,553 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1369

- Win Rate: 27.32%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -3.91434

- SQN Score: -16.25290


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 197 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 66 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 556 | 5 | 20.00% | **-0.00194** |  |
| CHOP_LOWVOL | 94078 | 1344 | 27.23% | **-0.00283** |  |
| PANIC | 916 | 20 | 35.00% | **-0.00507** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00290

- Last 20% Median Exp: -0.00256

- Drop Ratio: 11.93%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
