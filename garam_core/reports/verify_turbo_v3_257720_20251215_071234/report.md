# Turbo V3 Verified Result (257720)

## Meta

- Run ID: `verify_turbo_v3_257720_20251215_071234`
- Timestamp (UTC): `2025-12-15T07:12:34Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `257720` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2510, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3087904.841680612

## Key Points

- Total Return: -96.91%
- Max Drawdown: -97.12%
- Trades: 2510
- Final Equity: 3,087,905 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1255

- Win Rate: 28.05%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00046

- **Expectancy (Net)**: **-0.00234**

- Net PnL Total: -2.93757

- SQN Score: -6.94734


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 192 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 330 | 1 | 0.00% | **-0.01407** |  |
| CHOP_HIGHVOL | 11295 | 104 | 26.92% | **-0.00305** |  |
| CHOP_LOWVOL | 82833 | 1123 | 28.05% | **-0.00223** |  |
| PANIC | 1244 | 27 | 33.33% | **-0.00372** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00223

- Last 20% Median Exp: -0.00300

- Drop Ratio: -34.20%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
