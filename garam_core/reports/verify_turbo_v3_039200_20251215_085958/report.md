# Turbo V3 Verified Result (039200)

## Meta

- Run ID: `verify_turbo_v3_039200_20251215_085958`
- Timestamp (UTC): `2025-12-15T08:59:58Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `039200` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2737, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1593545.334430824

## Key Points

- Total Return: -98.41%
- Max Drawdown: -98.44%
- Trades: 2737
- Final Equity: 1,593,545 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1368

- Win Rate: 28.14%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00004

- **Expectancy (Net)**: **-0.00276**

- Net PnL Total: -3.77055

- SQN Score: -11.21148


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 106 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7779 | 102 | 27.45% | **-0.00387** |  |
| CHOP_LOWVOL | 84369 | 1239 | 28.25% | **-0.00255** |  |
| PANIC | 1308 | 27 | 25.93% | **-0.00807** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00269

- Last 20% Median Exp: -0.00233

- Drop Ratio: 13.50%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
