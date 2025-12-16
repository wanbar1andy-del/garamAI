# Turbo V3 Verified Result (353200)

## Meta

- Run ID: `verify_turbo_v3_353200_20251215_075501`
- Timestamp (UTC): `2025-12-15T07:55:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `353200` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2504, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3616154.496983159

## Key Points

- Total Return: -96.38%
- Max Drawdown: -96.42%
- Trades: 2504
- Final Equity: 3,616,154 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1252

- Win Rate: 29.39%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00040

- **Expectancy (Net)**: **-0.00240**

- Net PnL Total: -3.00469

- SQN Score: -7.71280


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 494 | 4 | 0.00% | **-0.01676** |  |
| TREND_DOWN | 383 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 8606 | 98 | 26.53% | **-0.00351** |  |
| CHOP_LOWVOL | 84509 | 1126 | 29.66% | **-0.00234** |  |
| PANIC | 1391 | 24 | 33.33% | **0.00169** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00231

- Last 20% Median Exp: -0.00240

- Drop Ratio: -3.64%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
