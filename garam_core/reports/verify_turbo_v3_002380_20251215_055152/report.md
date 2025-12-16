# Turbo V3 Verified Result (002380)

## Meta

- Run ID: `verify_turbo_v3_002380_20251215_055152`
- Timestamp (UTC): `2025-12-15T05:51:52Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `002380` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3075, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1003124.8365113626

## Key Points

- Total Return: -99.00%
- Max Drawdown: -99.00%
- Trades: 3075
- Final Equity: 1,003,125 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1537

- Win Rate: 26.87%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00016

- **Expectancy (Net)**: **-0.00264**

- Net PnL Total: -4.05846

- SQN Score: -16.36866


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 79 | 1 | 100.00% | **0.01999** |  |
| TREND_DOWN | 134 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1804 | 19 | 21.05% | **-0.00499** |  |
| CHOP_LOWVOL | 92040 | 1496 | 26.74% | **-0.00264** |  |
| PANIC | 979 | 21 | 38.10% | **-0.00196** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00261

- Last 20% Median Exp: -0.00217

- Drop Ratio: 16.78%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
