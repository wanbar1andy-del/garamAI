# Turbo V3 Verified Result (302440)

## Meta

- Run ID: `verify_turbo_v3_302440_20251215_084114`
- Timestamp (UTC): `2025-12-15T08:41:14Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `302440` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2719, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1653176.9671676722

## Key Points

- Total Return: -98.35%
- Max Drawdown: -98.57%
- Trades: 2719
- Final Equity: 1,653,177 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1359

- Win Rate: 26.34%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00013

- **Expectancy (Net)**: **-0.00267**

- Net PnL Total: -3.63004

- SQN Score: -11.11581


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 215 | 2 | 0.00% | **-0.02065** |  |
| TREND_DOWN | 69 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1420 | 13 | 7.69% | **-0.00316** |  |
| CHOP_LOWVOL | 90890 | 1321 | 26.27% | **-0.00276** |  |
| PANIC | 1175 | 23 | 43.48% | **0.00400** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00282

- Last 20% Median Exp: -0.00233

- Drop Ratio: 17.43%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
