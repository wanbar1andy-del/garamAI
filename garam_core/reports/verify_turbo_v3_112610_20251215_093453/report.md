# Turbo V3 Verified Result (112610)

## Meta

- Run ID: `verify_turbo_v3_112610_20251215_093453`
- Timestamp (UTC): `2025-12-15T09:34:53Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `112610` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2632, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1762158.117687597

## Key Points

- Total Return: -98.24%
- Max Drawdown: -98.27%
- Trades: 2632
- Final Equity: 1,762,158 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1316

- Win Rate: 27.28%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00010

- **Expectancy (Net)**: **-0.00270**

- Net PnL Total: -3.54910

- SQN Score: -13.37075


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 100 | 2 | 100.00% | **0.02688** |  |
| TREND_DOWN | 177 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1572 | 17 | 29.41% | **-0.00445** |  |
| CHOP_LOWVOL | 92715 | 1279 | 27.05% | **-0.00272** |  |
| PANIC | 1139 | 18 | 33.33% | **-0.00243** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00270

- Last 20% Median Exp: -0.00260

- Drop Ratio: 3.67%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
