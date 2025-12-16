# Turbo V3 Verified Result (008770)

## Meta

- Run ID: `verify_turbo_v3_008770_20251215_094047`
- Timestamp (UTC): `2025-12-15T09:40:47Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `008770` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3090, win_rate=0.00%, pnl=None, mdd=0.00%, equity=919620.7811403032

## Key Points

- Total Return: -99.08%
- Max Drawdown: -99.09%
- Trades: 3090
- Final Equity: 919,621 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1545

- Win Rate: 28.28%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00005

- **Expectancy (Net)**: **-0.00275**

- Net PnL Total: -4.24389

- SQN Score: -22.06031


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 172 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 271 | 1 | 0.00% | **-0.00597** |  |
| CHOP_HIGHVOL | 242 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 93292 | 1516 | 28.03% | **-0.00280** |  |
| PANIC | 1097 | 28 | 42.86% | **0.00019** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00280

- Last 20% Median Exp: -0.00284

- Drop Ratio: -1.19%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
