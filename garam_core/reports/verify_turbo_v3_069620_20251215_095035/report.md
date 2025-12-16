# Turbo V3 Verified Result (069620)

## Meta

- Run ID: `verify_turbo_v3_069620_20251215_095035`
- Timestamp (UTC): `2025-12-15T09:50:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `069620` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2742, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2116409.74864816

## Key Points

- Total Return: -97.88%
- Max Drawdown: -97.89%
- Trades: 2742
- Final Equity: 2,116,410 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1371

- Win Rate: 33.55%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00041

- **Expectancy (Net)**: **-0.00239**

- Net PnL Total: -3.28179

- SQN Score: -11.69379


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 105 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 84 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1295 | 7 | 14.29% | **-0.01128** |  |
| CHOP_LOWVOL | 91125 | 1325 | 33.13% | **-0.00249** |  |
| PANIC | 1727 | 39 | 51.28% | **0.00233** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00255

- Last 20% Median Exp: -0.00200

- Drop Ratio: 21.47%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
