# Turbo V3 Verified Result (267250)

## Meta

- Run ID: `verify_turbo_v3_267250_20251215_012408`
- Timestamp (UTC): `2025-12-15T01:24:08Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `267250` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2882, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1407718.928877434

## Key Points

- Total Return: -98.59%
- Max Drawdown: -98.62%
- Trades: 2882
- Final Equity: 1,407,719 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1441

- Win Rate: 27.34%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00015

- **Expectancy (Net)**: **-0.00265**

- Net PnL Total: -3.81158

- SQN Score: -13.15707


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 290 | 3 | 66.67% | **0.00504** |  |
| TREND_DOWN | 203 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3051 | 26 | 19.23% | **-0.00437** |  |
| CHOP_LOWVOL | 91115 | 1385 | 27.22% | **-0.00264** |  |
| PANIC | 1193 | 27 | 37.04% | **-0.00207** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00277

- Last 20% Median Exp: -0.00276

- Drop Ratio: 0.47%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
