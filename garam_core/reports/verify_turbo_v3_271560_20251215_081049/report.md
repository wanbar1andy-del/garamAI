# Turbo V3 Verified Result (271560)

## Meta

- Run ID: `verify_turbo_v3_271560_20251215_081049`
- Timestamp (UTC): `2025-12-15T08:10:49Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `271560` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2970, win_rate=0.00%, pnl=None, mdd=0.00%, equity=912801.3901177712

## Key Points

- Total Return: -99.09%
- Max Drawdown: -99.09%
- Trades: 2970
- Final Equity: 912,801 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1485

- Win Rate: 29.63%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00009

- **Expectancy (Net)**: **-0.00289**

- Net PnL Total: -4.29329

- SQN Score: -27.61339


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 22 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 64 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 352 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94108 | 1456 | 29.40% | **-0.00289** |  |
| PANIC | 1272 | 29 | 41.38% | **-0.00287** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00276

- Last 20% Median Exp: -0.00303

- Drop Ratio: -9.52%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
