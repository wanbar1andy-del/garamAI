# Turbo V3 Verified Result (052690)

## Meta

- Run ID: `verify_turbo_v3_052690_20251215_053235`
- Timestamp (UTC): `2025-12-15T05:32:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `052690` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2702, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1374396.7628717902

## Key Points

- Total Return: -98.63%
- Max Drawdown: -98.64%
- Trades: 2702
- Final Equity: 1,374,397 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1351

- Win Rate: 27.46%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -3.86812

- SQN Score: -8.57916


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 264 | 1 | 100.00% | **0.07458** |  |
| TREND_DOWN | 200 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4615 | 45 | 26.67% | **-0.00306** |  |
| CHOP_LOWVOL | 88202 | 1278 | 27.23% | **-0.00284** |  |
| PANIC | 1078 | 27 | 37.04% | **-0.00645** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00283

- Last 20% Median Exp: -0.00306

- Drop Ratio: -8.25%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
