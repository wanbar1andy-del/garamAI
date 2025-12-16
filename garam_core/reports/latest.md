# Turbo V3 Verified Result (103140)

## Meta

- Run ID: `verify_turbo_v3_103140_20251215_100931`
- Timestamp (UTC): `2025-12-15T10:09:31Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `103140` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2670, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2024256.7800720884

## Key Points

- Total Return: -97.98%
- Max Drawdown: -98.02%
- Trades: 2670
- Final Equity: 2,024,257 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1335

- Win Rate: 26.82%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00012

- **Expectancy (Net)**: **-0.00268**

- Net PnL Total: -3.57898

- SQN Score: -9.86068


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 149 | 4 | 0.00% | **-0.02134** |  |
| TREND_DOWN | 507 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4469 | 33 | 42.42% | **-0.00343** |  |
| CHOP_LOWVOL | 89455 | 1273 | 26.16% | **-0.00260** |  |
| PANIC | 1244 | 25 | 44.00% | **-0.00275** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00279

- Last 20% Median Exp: -0.00239

- Drop Ratio: 14.08%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
