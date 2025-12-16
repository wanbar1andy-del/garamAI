# Turbo V3 Verified Result (263750)

## Meta

- Run ID: `verify_turbo_v3_263750_20251215_064504`
- Timestamp (UTC): `2025-12-15T06:45:04Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `263750` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3033, win_rate=0.00%, pnl=None, mdd=0.00%, equity=642897.9698202999

## Key Points

- Total Return: -99.36%
- Max Drawdown: -99.36%
- Trades: 3033
- Final Equity: 642,898 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1516

- Win Rate: 26.32%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00012

- **Expectancy (Net)**: **-0.00292**

- Net PnL Total: -4.43429

- SQN Score: -13.59906


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 43 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 186 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1480 | 9 | 22.22% | **-0.00380** |  |
| CHOP_LOWVOL | 91343 | 1478 | 25.78% | **-0.00299** |  |
| PANIC | 1035 | 29 | 55.17% | **0.00082** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00324

- Last 20% Median Exp: -0.00247

- Drop Ratio: 23.75%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
