# Turbo V3 Verified Result (018880)

## Meta

- Run ID: `verify_turbo_v3_018880_20251215_090519`
- Timestamp (UTC): `2025-12-15T09:05:19Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `018880` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2911, win_rate=0.00%, pnl=None, mdd=0.00%, equity=753825.8194873953

## Key Points

- Total Return: -99.25%
- Max Drawdown: -99.26%
- Trades: 2911
- Final Equity: 753,826 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1455

- Win Rate: 26.12%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00022

- **Expectancy (Net)**: **-0.00302**

- Net PnL Total: -4.39306

- SQN Score: -18.22114


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 71 | 2 | 50.00% | **-0.01463** |  |
| TREND_DOWN | 104 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2271 | 11 | 27.27% | **0.00016** |  |
| CHOP_LOWVOL | 91743 | 1413 | 25.76% | **-0.00307** |  |
| PANIC | 1189 | 29 | 41.38% | **-0.00118** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00286

- Last 20% Median Exp: -0.00273

- Drop Ratio: 4.52%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
