# Turbo V3 Verified Result (035900)

## Meta

- Run ID: `verify_turbo_v3_035900_20251215_094222`
- Timestamp (UTC): `2025-12-15T09:42:22Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `035900` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2834, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1113718.548052974

## Key Points

- Total Return: -98.89%
- Max Drawdown: -98.89%
- Trades: 2834
- Final Equity: 1,113,719 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1417

- Win Rate: 27.17%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00001

- **Expectancy (Net)**: **-0.00281**

- Net PnL Total: -3.98694

- SQN Score: -17.31531


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 111 | 3 | 0.00% | **-0.01181** |  |
| TREND_DOWN | 185 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1100 | 6 | 16.67% | **-0.00647** |  |
| CHOP_LOWVOL | 93576 | 1389 | 27.00% | **-0.00282** |  |
| PANIC | 923 | 19 | 47.37% | **0.00005** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00274

- Last 20% Median Exp: -0.00310

- Drop Ratio: -13.13%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
