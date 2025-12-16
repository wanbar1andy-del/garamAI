# Turbo V3 Verified Result (011070)

## Meta

- Run ID: `verify_turbo_v3_011070_20251215_014824`
- Timestamp (UTC): `2025-12-15T01:48:24Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `011070` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2424, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3190485.1124887145

## Key Points

- Total Return: -96.81%
- Max Drawdown: -96.82%
- Trades: 2424
- Final Equity: 3,190,485 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1212

- Win Rate: 27.89%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00038

- **Expectancy (Net)**: **-0.00242**

- Net PnL Total: -2.93531

- SQN Score: -9.61971


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 819 | 7 | 57.14% | **0.01018** |  |
| TREND_DOWN | 1040 | 5 | 20.00% | **-0.00371** |  |
| CHOP_HIGHVOL | 985 | 10 | 30.00% | **0.00050** |  |
| CHOP_LOWVOL | 91657 | 1163 | 27.52% | **-0.00254** |  |
| PANIC | 1354 | 27 | 37.04% | **-0.00130** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00240

- Last 20% Median Exp: -0.00281

- Drop Ratio: -16.77%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
