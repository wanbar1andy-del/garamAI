# Turbo V3 Verified Result (087010)

## Meta

- Run ID: `verify_turbo_v3_087010_20251215_012325`
- Timestamp (UTC): `2025-12-15T01:23:25Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `087010` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2393, win_rate=0.00%, pnl=None, mdd=0.00%, equity=5368199.7838516

## Key Points

- Total Return: -94.63%
- Max Drawdown: -94.92%
- Trades: 2393
- Final Equity: 5,368,200 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1196

- Win Rate: 30.10%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00090

- **Expectancy (Net)**: **-0.00190**

- Net PnL Total: -2.27025

- SQN Score: -3.64126


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 258 | 2 | 100.00% | **0.05559** |  |
| TREND_DOWN | 223 | 1 | 0.00% | **-0.00528** |  |
| CHOP_HIGHVOL | 14013 | 143 | 33.57% | **-0.00382** |  |
| CHOP_LOWVOL | 79605 | 1028 | 29.09% | **-0.00204** |  |
| PANIC | 1614 | 22 | 50.00% | **0.01197** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00193

- Last 20% Median Exp: -0.00198

- Drop Ratio: -2.30%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
