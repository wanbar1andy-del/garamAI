# Turbo V3 Verified Result (005930)

## Meta

- Run ID: `verify_turbo_v3_005930_20251214_203149`
- Timestamp (UTC): `2025-12-14T20:31:49Z`
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

- Trades: 738

- Win Rate: 0.00%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -2.06640

- SQN Score: -175394490738698592.00000


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **OVERTRADING**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 213 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 290 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 104 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94350 | 0 | 0.00% | **0.00000** |  |
| PANIC | 858 | 0 | 0.00% | **0.00000** |  |
| UNCERTAIN | 0 | 738 | 0.00% | **-0.00280** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00280

- Last 20% Median Exp: -0.00280

- Drop Ratio: 0.00%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
