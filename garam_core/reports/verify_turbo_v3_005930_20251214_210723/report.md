# Turbo V3 Verified Result (005930)

## Meta

- Run ID: `verify_turbo_v3_005930_20251214_210723`
- Timestamp (UTC): `2025-12-14T21:07:23Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005930` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=738, win_rate=0.00%, pnl=None, mdd=0.00%, equity=32916426.399889644

## Key Points

- Total Return: -67.08%
- Max Drawdown: -67.52%
- Trades: 738
- Final Equity: 32,916,426 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 369

- Win Rate: 22.22%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00002

- **Expectancy (Net)**: **-0.00278**

- Net PnL Total: -1.02578

- SQN Score: -11.96828


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **OVERTRADING**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 285 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 210 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94626 | 0 | 0.00% | **0.00000** |  |
| PANIC | 694 | 0 | 0.00% | **0.00000** |  |
| UNCERTAIN | 0 | 369 | 22.22% | **-0.00278** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00282

- Last 20% Median Exp: -0.00285

- Drop Ratio: -1.05%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
