# Turbo V3 Verified Result (034020)

## Meta

- Run ID: `verify_turbo_v3_034020_20251215_025241`
- Timestamp (UTC): `2025-12-15T02:52:41Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `034020` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2606, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3389004.7854098915

## Key Points

- Total Return: -96.61%
- Max Drawdown: -96.66%
- Trades: 2606
- Final Equity: 3,389,005 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1303

- Win Rate: 29.62%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00055

- **Expectancy (Net)**: **-0.00225**

- Net PnL Total: -2.92670

- SQN Score: -8.00768


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 140 | 2 | 0.00% | **-0.02814** |  |
| TREND_DOWN | 254 | 1 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 5959 | 57 | 35.09% | **-0.00234** |  |
| CHOP_LOWVOL | 88540 | 1227 | 29.10% | **-0.00225** |  |
| PANIC | 997 | 16 | 56.25% | **0.00153** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00224

- Last 20% Median Exp: -0.00285

- Drop Ratio: -27.28%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
