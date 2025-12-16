# Turbo V3 Verified Result (086520)

## Meta

- Run ID: `verify_turbo_v3_086520_20251215_014828`
- Timestamp (UTC): `2025-12-15T01:48:28Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `086520` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2497, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2999106.9062395147

## Key Points

- Total Return: -97.00%
- Max Drawdown: -97.31%
- Trades: 2497
- Final Equity: 2,999,107 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1248

- Win Rate: 25.32%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00031

- **Expectancy (Net)**: **-0.00249**

- Net PnL Total: -3.10707

- SQN Score: -6.25447


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 258 | 3 | 33.33% | **-0.00591** |  |
| TREND_DOWN | 182 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4944 | 34 | 32.35% | **-0.00264** |  |
| CHOP_LOWVOL | 88157 | 1186 | 24.87% | **-0.00247** |  |
| PANIC | 1224 | 25 | 36.00% | **-0.00297** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00297

- Last 20% Median Exp: -0.00073

- Drop Ratio: 75.40%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
