# Turbo V3 Verified Result (138930)

## Meta

- Run ID: `verify_turbo_v3_138930_20251215_043632`
- Timestamp (UTC): `2025-12-15T04:36:32Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `138930` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2755, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1988122.6420672028

## Key Points

- Total Return: -98.01%
- Max Drawdown: -98.19%
- Trades: 2755
- Final Equity: 1,988,123 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1377

- Win Rate: 30.28%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00016

- **Expectancy (Net)**: **-0.00264**

- Net PnL Total: -3.63355

- SQN Score: -17.94751


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 205 | 2 | 0.00% | **-0.00951** |  |
| TREND_DOWN | 296 | 1 | 0.00% | **-0.00380** |  |
| CHOP_HIGHVOL | 93 | 2 | 0.00% | **-0.00637** |  |
| CHOP_LOWVOL | 93817 | 1345 | 30.33% | **-0.00263** |  |
| PANIC | 1441 | 27 | 33.33% | **-0.00206** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00268

- Last 20% Median Exp: -0.00254

- Drop Ratio: 5.25%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
