# Turbo V3 Verified Result (241560)

## Meta

- Run ID: `verify_turbo_v3_241560_20251215_014844`
- Timestamp (UTC): `2025-12-15T01:48:44Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `241560` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2940, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1045007.4494805499

## Key Points

- Total Return: -98.95%
- Max Drawdown: -99.02%
- Trades: 2940
- Final Equity: 1,045,007 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1470

- Win Rate: 24.90%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00008

- **Expectancy (Net)**: **-0.00288**

- Net PnL Total: -4.24064

- SQN Score: -14.79392


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 126 | 2 | 50.00% | **0.01468** |  |
| TREND_DOWN | 119 | 1 | 100.00% | **0.01381** |  |
| CHOP_HIGHVOL | 2243 | 20 | 25.00% | **-0.00807** |  |
| CHOP_LOWVOL | 92315 | 1426 | 24.68% | **-0.00284** |  |
| PANIC | 1026 | 21 | 33.33% | **-0.00376** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00307

- Last 20% Median Exp: -0.00295

- Drop Ratio: 4.00%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
