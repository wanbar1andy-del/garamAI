# Turbo V3 Verified Result (083650)

## Meta

- Run ID: `verify_turbo_v3_083650_20251215_084010`
- Timestamp (UTC): `2025-12-15T08:40:10Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `083650` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2466, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2283515.9917105534

## Key Points

- Total Return: -97.72%
- Max Drawdown: -98.15%
- Trades: 2466
- Final Equity: 2,283,516 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1233

- Win Rate: 28.55%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00034

- **Expectancy (Net)**: **-0.00246**

- Net PnL Total: -3.03763

- SQN Score: -6.31132


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 194 | 5 | 40.00% | **-0.00115** |  |
| TREND_DOWN | 195 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 21438 | 215 | 32.56% | **-0.00110** |  |
| CHOP_LOWVOL | 72569 | 981 | 27.93% | **-0.00251** |  |
| PANIC | 1468 | 32 | 18.75% | **-0.01036** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00250

- Last 20% Median Exp: -0.00327

- Drop Ratio: -31.12%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
