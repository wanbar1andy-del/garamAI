# Turbo V3 Verified Result (067310)

## Meta

- Run ID: `verify_turbo_v3_067310_20251215_090547`
- Timestamp (UTC): `2025-12-15T09:05:47Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `067310` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2536, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2650366.210797627

## Key Points

- Total Return: -97.35%
- Max Drawdown: -97.43%
- Trades: 2536
- Final Equity: 2,650,366 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1268

- Win Rate: 29.26%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00029

- **Expectancy (Net)**: **-0.00251**

- Net PnL Total: -3.17908

- SQN Score: -7.56257


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **STRUCTURAL_BREAK**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 354 | 4 | 100.00% | **0.02064** |  |
| TREND_DOWN | 368 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 10313 | 115 | 37.39% | **-0.00205** |  |
| CHOP_LOWVOL | 83211 | 1128 | 27.84% | **-0.00261** |  |
| PANIC | 1290 | 21 | 47.62% | **-0.00377** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00204

- Last 20% Median Exp: -0.00363

- Drop Ratio: -78.01%

- **Structural Break**: **YES**

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
