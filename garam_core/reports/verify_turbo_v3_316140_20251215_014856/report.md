# Turbo V3 Verified Result (316140)

## Meta

- Run ID: `verify_turbo_v3_316140_20251215_014856`
- Timestamp (UTC): `2025-12-15T01:48:56Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `316140` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3192, win_rate=0.00%, pnl=None, mdd=0.00%, equity=743745.3372331552

## Key Points

- Total Return: -99.26%
- Max Drawdown: -99.26%
- Trades: 3192
- Final Equity: 743,745 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1596

- Win Rate: 28.13%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -4.46461

- SQN Score: -20.88476


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 322 | 2 | 50.00% | **-0.01200** |  |
| TREND_DOWN | 113 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 115 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94460 | 1574 | 28.02% | **-0.00277** |  |
| PANIC | 876 | 20 | 35.00% | **-0.00428** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00269

- Last 20% Median Exp: -0.00276

- Drop Ratio: -2.40%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
