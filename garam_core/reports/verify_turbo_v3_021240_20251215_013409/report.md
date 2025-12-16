# Turbo V3 Verified Result (021240)

## Meta

- Run ID: `verify_turbo_v3_021240_20251215_013409`
- Timestamp (UTC): `2025-12-15T01:34:09Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `021240` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2949, win_rate=0.00%, pnl=None, mdd=0.00%, equity=602828.0232561865

## Key Points

- Total Return: -99.40%
- Max Drawdown: -99.40%
- Trades: 2949
- Final Equity: 602,828 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1474

- Win Rate: 26.46%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00048

- **Expectancy (Net)**: **-0.00328**

- Net PnL Total: -4.83194

- SQN Score: -18.08915


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 355 | 3 | 100.00% | **0.03049** |  |
| TREND_DOWN | 12 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2085 | 24 | 29.17% | **-0.00449** |  |
| CHOP_LOWVOL | 91881 | 1429 | 25.96% | **-0.00336** |  |
| PANIC | 1401 | 18 | 50.00% | **-0.00052** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00323

- Last 20% Median Exp: -0.00337

- Drop Ratio: -4.47%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
