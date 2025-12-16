# Turbo V3 Verified Result (259960)

## Meta

- Run ID: `verify_turbo_v3_259960_20251215_011355`
- Timestamp (UTC): `2025-12-15T01:13:55Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `259960` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2939, win_rate=0.00%, pnl=None, mdd=0.00%, equity=575261.2642749476

## Key Points

- Total Return: -99.42%
- Max Drawdown: -99.44%
- Trades: 2939
- Final Equity: 575,261 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1469

- Win Rate: 25.66%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00037

- **Expectancy (Net)**: **-0.00317**

- Net PnL Total: -4.65153

- SQN Score: -20.74329


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 63 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 254 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 503 | 4 | 50.00% | **-0.00570** |  |
| CHOP_LOWVOL | 94008 | 1441 | 25.47% | **-0.00313** |  |
| PANIC | 919 | 24 | 33.33% | **-0.00517** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00319

- Last 20% Median Exp: -0.00338

- Drop Ratio: -5.67%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
