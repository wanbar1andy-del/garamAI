# Turbo V3 Verified Result (071050)

## Meta

- Run ID: `verify_turbo_v3_071050_20251215_010251`
- Timestamp (UTC): `2025-12-15T01:02:51Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `071050` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2911, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1736934.6229979303

## Key Points

- Total Return: -98.26%
- Max Drawdown: -98.37%
- Trades: 2911
- Final Equity: 1,736,935 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1455

- Win Rate: 31.96%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00035

- **Expectancy (Net)**: **-0.00245**

- Net PnL Total: -3.56453

- SQN Score: -11.85875


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 246 | 1 | 0.00% | **-0.00365** |  |
| TREND_DOWN | 103 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1483 | 18 | 50.00% | **-0.00062** |  |
| CHOP_LOWVOL | 92736 | 1418 | 31.59% | **-0.00251** |  |
| PANIC | 1181 | 18 | 44.44% | **0.00014** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00255

- Last 20% Median Exp: -0.00211

- Drop Ratio: 16.97%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
