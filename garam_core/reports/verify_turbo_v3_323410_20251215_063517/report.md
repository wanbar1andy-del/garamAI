# Turbo V3 Verified Result (323410)

## Meta

- Run ID: `verify_turbo_v3_323410_20251215_063517`
- Timestamp (UTC): `2025-12-15T06:35:17Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `323410` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3484, win_rate=0.00%, pnl=None, mdd=0.00%, equity=279891.6226922234

## Key Points

- Total Return: -99.72%
- Max Drawdown: -99.72%
- Trades: 3484
- Final Equity: 279,892 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1742

- Win Rate: 23.71%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00030

- **Expectancy (Net)**: **-0.00310**

- Net PnL Total: -5.39821

- SQN Score: -16.44840


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 95 | 1 | 0.00% | **-0.04532** |  |
| TREND_DOWN | 20 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2496 | 23 | 21.74% | **-0.00575** |  |
| CHOP_LOWVOL | 91460 | 1702 | 23.56% | **-0.00304** |  |
| PANIC | 660 | 16 | 43.75% | **-0.00273** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00308

- Last 20% Median Exp: -0.00330

- Drop Ratio: -6.87%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
