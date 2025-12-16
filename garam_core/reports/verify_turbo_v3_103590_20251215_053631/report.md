# Turbo V3 Verified Result (103590)

## Meta

- Run ID: `verify_turbo_v3_103590_20251215_053631`
- Timestamp (UTC): `2025-12-15T05:36:31Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `103590` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2577, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2668742.5428336514

## Key Points

- Total Return: -97.33%
- Max Drawdown: -97.41%
- Trades: 2577
- Final Equity: 2,668,743 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1288

- Win Rate: 28.88%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00044

- **Expectancy (Net)**: **-0.00236**

- Net PnL Total: -3.03804

- SQN Score: -7.11468


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 219 | 2 | 100.00% | **0.00041** |  |
| TREND_DOWN | 111 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 10063 | 94 | 23.40% | **-0.00582** |  |
| CHOP_LOWVOL | 84426 | 1163 | 28.98% | **-0.00204** |  |
| PANIC | 1062 | 29 | 37.93% | **-0.00429** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00215

- Last 20% Median Exp: -0.00298

- Drop Ratio: -38.47%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
