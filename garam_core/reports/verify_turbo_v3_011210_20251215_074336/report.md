# Turbo V3 Verified Result (011210)

## Meta

- Run ID: `verify_turbo_v3_011210_20251215_074336`
- Timestamp (UTC): `2025-12-15T07:43:36Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `011210` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2925, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1187595.5419363522

## Key Points

- Total Return: -98.81%
- Max Drawdown: -98.84%
- Trades: 2925
- Final Equity: 1,187,596 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1462

- Win Rate: 26.27%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00003

- **Expectancy (Net)**: **-0.00277**

- Net PnL Total: -4.05382

- SQN Score: -18.61799


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 124 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 16 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 495 | 6 | 33.33% | **-0.00342** |  |
| CHOP_LOWVOL | 91783 | 1434 | 26.15% | **-0.00279** |  |
| PANIC | 1088 | 22 | 31.82% | **-0.00151** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00271

- Last 20% Median Exp: -0.00302

- Drop Ratio: -11.55%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
