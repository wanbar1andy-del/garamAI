# Turbo V3 Verified Result (267260)

## Meta

- Run ID: `verify_turbo_v3_267260_20251215_014809`
- Timestamp (UTC): `2025-12-15T01:48:09Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `267260` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2631, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2807779.2700047367

## Key Points

- Total Return: -97.19%
- Max Drawdown: -97.28%
- Trades: 2631
- Final Equity: 2,807,779 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1315

- Win Rate: 29.43%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00031

- **Expectancy (Net)**: **-0.00249**

- Net PnL Total: -3.27569

- SQN Score: -9.27164


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 228 | 4 | 25.00% | **-0.00213** |  |
| TREND_DOWN | 377 | 1 | 100.00% | **-0.00139** |  |
| CHOP_HIGHVOL | 1761 | 14 | 21.43% | **-0.00459** |  |
| CHOP_LOWVOL | 92373 | 1281 | 29.43% | **-0.00242** |  |
| PANIC | 1145 | 15 | 33.33% | **-0.00655** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00253

- Last 20% Median Exp: -0.00235

- Drop Ratio: 7.12%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
