# Turbo V3 Verified Result (023590)

## Meta

- Run ID: `verify_turbo_v3_023590_20251215_065334`
- Timestamp (UTC): `2025-12-15T06:53:34Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `023590` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2702, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1993909.943617511

## Key Points

- Total Return: -98.01%
- Max Drawdown: -98.17%
- Trades: 2702
- Final Equity: 1,993,910 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1351

- Win Rate: 28.05%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00022

- **Expectancy (Net)**: **-0.00258**

- Net PnL Total: -3.48151

- SQN Score: -13.42671


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 176 | 2 | 50.00% | **0.00299** |  |
| TREND_DOWN | 92 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 987 | 10 | 40.00% | **0.00141** |  |
| CHOP_LOWVOL | 86880 | 1314 | 27.63% | **-0.00273** |  |
| PANIC | 1204 | 25 | 44.00% | **0.00330** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00268

- Last 20% Median Exp: -0.00252

- Drop Ratio: 5.99%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
