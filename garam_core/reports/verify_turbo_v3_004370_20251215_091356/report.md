# Turbo V3 Verified Result (004370)

## Meta

- Run ID: `verify_turbo_v3_004370_20251215_091356`
- Timestamp (UTC): `2025-12-15T09:13:56Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `004370` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2984, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1037205.5358803958

## Key Points

- Total Return: -98.96%
- Max Drawdown: -98.96%
- Trades: 2984
- Final Equity: 1,037,206 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1492

- Win Rate: 27.68%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00010

- **Expectancy (Net)**: **-0.00270**

- Net PnL Total: -4.03097

- SQN Score: -16.32237


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 265 | 2 | 100.00% | **0.01382** |  |
| TREND_DOWN | 53 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 923 | 7 | 14.29% | **-0.00726** |  |
| CHOP_LOWVOL | 93100 | 1458 | 27.30% | **-0.00270** |  |
| PANIC | 1040 | 25 | 48.00% | **-0.00264** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00261

- Last 20% Median Exp: -0.00285

- Drop Ratio: -9.18%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
