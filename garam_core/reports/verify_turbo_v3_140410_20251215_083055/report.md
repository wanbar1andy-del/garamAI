# Turbo V3 Verified Result (140410)

## Meta

- Run ID: `verify_turbo_v3_140410_20251215_083055`
- Timestamp (UTC): `2025-12-15T08:30:55Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `140410` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2191, win_rate=0.00%, pnl=None, mdd=0.00%, equity=9753219.053451486

## Key Points

- Total Return: -90.25%
- Max Drawdown: -90.47%
- Trades: 2191
- Final Equity: 9,753,219 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1095

- Win Rate: 27.49%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00097

- **Expectancy (Net)**: **-0.00183**

- Net PnL Total: -2.00922

- SQN Score: -5.11021


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 170 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 76 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2221 | 14 | 14.29% | **-0.00741** |  |
| CHOP_LOWVOL | 79806 | 1060 | 27.45% | **-0.00172** |  |
| PANIC | 1362 | 21 | 38.10% | **-0.00400** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00211

- Last 20% Median Exp: -0.00143

- Drop Ratio: 32.21%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
