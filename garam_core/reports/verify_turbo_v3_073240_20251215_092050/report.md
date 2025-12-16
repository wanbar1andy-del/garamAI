# Turbo V3 Verified Result (073240)

## Meta

- Run ID: `verify_turbo_v3_073240_20251215_092050`
- Timestamp (UTC): `2025-12-15T09:20:50Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `073240` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2971, win_rate=0.00%, pnl=None, mdd=0.00%, equity=967926.3462901535

## Key Points

- Total Return: -99.03%
- Max Drawdown: -99.04%
- Trades: 2971
- Final Equity: 967,926 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1485

- Win Rate: 27.21%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00018

- **Expectancy (Net)**: **-0.00298**

- Net PnL Total: -4.42501

- SQN Score: -22.55806


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 85 | 1 | 100.00% | **0.00600** |  |
| TREND_DOWN | 4 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1156 | 9 | 44.44% | **0.00077** |  |
| CHOP_LOWVOL | 91479 | 1441 | 26.58% | **-0.00301** |  |
| PANIC | 1326 | 34 | 47.06% | **-0.00275** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00294

- Last 20% Median Exp: -0.00307

- Drop Ratio: -4.52%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
