# Turbo V3 Verified Result (058610)

## Meta

- Run ID: `verify_turbo_v3_058610_20251215_082629`
- Timestamp (UTC): `2025-12-15T08:26:29Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `058610` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2693, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1902706.0927157588

## Key Points

- Total Return: -98.10%
- Max Drawdown: -98.45%
- Trades: 2693
- Final Equity: 1,902,706 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1346

- Win Rate: 25.71%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00025

- **Expectancy (Net)**: **-0.00255**

- Net PnL Total: -3.43414

- SQN Score: -7.21695


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 146 | 2 | 50.00% | **0.00252** |  |
| TREND_DOWN | 8 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 8186 | 78 | 26.92% | **-0.00269** |  |
| CHOP_LOWVOL | 83572 | 1246 | 25.60% | **-0.00261** |  |
| PANIC | 1009 | 20 | 25.00% | **0.00127** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00271

- Last 20% Median Exp: -0.00318

- Drop Ratio: -17.20%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
