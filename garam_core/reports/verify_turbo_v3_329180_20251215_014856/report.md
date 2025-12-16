# Turbo V3 Verified Result (329180)

## Meta

- Run ID: `verify_turbo_v3_329180_20251215_014856`
- Timestamp (UTC): `2025-12-15T01:48:56Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `329180` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2630, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2656350.1974823945

## Key Points

- Total Return: -97.34%
- Max Drawdown: -97.35%
- Trades: 2630
- Final Equity: 2,656,350 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1315

- Win Rate: 30.11%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00048

- **Expectancy (Net)**: **-0.00232**

- Net PnL Total: -3.05682

- SQN Score: -8.58965


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 245 | 2 | 0.00% | **-0.01686** |  |
| TREND_DOWN | 159 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3745 | 39 | 35.90% | **-0.00118** |  |
| CHOP_LOWVOL | 90620 | 1248 | 30.05% | **-0.00228** |  |
| PANIC | 1120 | 26 | 26.92% | **-0.00526** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00228

- Last 20% Median Exp: -0.00273

- Drop Ratio: -19.56%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
