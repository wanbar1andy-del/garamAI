# Turbo V3 Verified Result (141080)

## Meta

- Run ID: `verify_turbo_v3_141080_20251215_063631`
- Timestamp (UTC): `2025-12-15T06:36:31Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `141080` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2272, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3459691.2704032646

## Key Points

- Total Return: -96.54%
- Max Drawdown: -96.67%
- Trades: 2272
- Final Equity: 3,459,691 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1136

- Win Rate: 28.79%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00025

- **Expectancy (Net)**: **-0.00255**

- Net PnL Total: -2.90142

- SQN Score: -9.06936


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 226 | 1 | 0.00% | **-0.01290** |  |
| TREND_DOWN | 195 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2609 | 18 | 27.78% | **-0.00365** |  |
| CHOP_LOWVOL | 91356 | 1085 | 28.11% | **-0.00256** |  |
| PANIC | 1511 | 32 | 53.12% | **-0.00135** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00243

- Last 20% Median Exp: -0.00282

- Drop Ratio: -15.96%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
