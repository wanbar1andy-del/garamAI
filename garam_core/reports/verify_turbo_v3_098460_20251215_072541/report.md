# Turbo V3 Verified Result (098460)

## Meta

- Run ID: `verify_turbo_v3_098460_20251215_072541`
- Timestamp (UTC): `2025-12-15T07:25:41Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `098460` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2518, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2844427.370639844

## Key Points

- Total Return: -97.16%
- Max Drawdown: -97.38%
- Trades: 2518
- Final Equity: 2,844,427 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1259

- Win Rate: 26.37%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00043

- **Expectancy (Net)**: **-0.00237**

- Net PnL Total: -2.98259

- SQN Score: -4.62104


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 310 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 164 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 8746 | 74 | 27.03% | **-0.00113** |  |
| CHOP_LOWVOL | 84877 | 1156 | 26.21% | **-0.00257** |  |
| PANIC | 1465 | 29 | 31.03% | **0.00263** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00320

- Last 20% Median Exp: -0.00202

- Drop Ratio: 36.83%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
