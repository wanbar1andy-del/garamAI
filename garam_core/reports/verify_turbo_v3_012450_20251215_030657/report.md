# Turbo V3 Verified Result (012450)

## Meta

- Run ID: `verify_turbo_v3_012450_20251215_030657`
- Timestamp (UTC): `2025-12-15T03:06:57Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `012450` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2494, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4847714.720617047

## Key Points

- Total Return: -95.15%
- Max Drawdown: -95.43%
- Trades: 2494
- Final Equity: 4,847,715 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1247

- Win Rate: 32.00%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00079

- **Expectancy (Net)**: **-0.00201**

- Net PnL Total: -2.51223

- SQN Score: -7.76965


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 266 | 3 | 0.00% | **-0.02073** |  |
| TREND_DOWN | 264 | 1 | 100.00% | **0.03102** |  |
| CHOP_HIGHVOL | 3040 | 33 | 45.45% | **0.00078** |  |
| CHOP_LOWVOL | 90971 | 1179 | 31.04% | **-0.00223** |  |
| PANIC | 1346 | 31 | 54.84% | **0.00389** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00188

- Last 20% Median Exp: -0.00264

- Drop Ratio: -40.52%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
