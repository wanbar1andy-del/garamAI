# Turbo V3 Verified Result (003570)

## Meta

- Run ID: `verify_turbo_v3_003570_20251215_091510`
- Timestamp (UTC): `2025-12-15T09:15:10Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `003570` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2698, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2649169.9220475703

## Key Points

- Total Return: -97.35%
- Max Drawdown: -97.51%
- Trades: 2698
- Final Equity: 2,649,170 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1349

- Win Rate: 30.54%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00057

- **Expectancy (Net)**: **-0.00223**

- Net PnL Total: -3.00257

- SQN Score: -7.99315


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **STRUCTURAL_BREAK**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 61 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 29 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 15025 | 165 | 33.94% | **-0.00218** |  |
| CHOP_LOWVOL | 78229 | 1156 | 29.41% | **-0.00234** |  |
| PANIC | 1433 | 28 | 57.14% | **0.00204** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00179

- Last 20% Median Exp: -0.00311

- Drop Ratio: -73.59%

- **Structural Break**: **YES**

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
