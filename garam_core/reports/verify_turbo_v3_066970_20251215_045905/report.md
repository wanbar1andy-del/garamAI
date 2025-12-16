# Turbo V3 Verified Result (066970)

## Meta

- Run ID: `verify_turbo_v3_066970_20251215_045905`
- Timestamp (UTC): `2025-12-15T04:59:05Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `066970` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2430, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3944063.765281169

## Key Points

- Total Return: -96.06%
- Max Drawdown: -96.50%
- Trades: 2430
- Final Equity: 3,944,064 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1215

- Win Rate: 26.75%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00023

- **Expectancy (Net)**: **-0.00257**

- Net PnL Total: -3.12588

- SQN Score: -6.39320


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 319 | 3 | 33.33% | **-0.00889** |  |
| TREND_DOWN | 354 | 1 | 0.00% | **-0.01075** |  |
| CHOP_HIGHVOL | 9657 | 100 | 28.00% | **-0.00212** |  |
| CHOP_LOWVOL | 84273 | 1083 | 26.69% | **-0.00255** |  |
| PANIC | 1262 | 28 | 25.00% | **-0.00396** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00274

- Last 20% Median Exp: -0.00091

- Drop Ratio: 66.56%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
