# Turbo V3 Verified Result (001430)

## Meta

- Run ID: `verify_turbo_v3_001430_20251215_100446`
- Timestamp (UTC): `2025-12-15T10:04:46Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `001430` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2879, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1032818.5197779211

## Key Points

- Total Return: -98.97%
- Max Drawdown: -99.05%
- Trades: 2879
- Final Equity: 1,032,819 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1439

- Win Rate: 28.42%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00016

- **Expectancy (Net)**: **-0.00296**

- Net PnL Total: -4.25417

- SQN Score: -14.86421


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 43 | 1 | 100.00% | **0.00451** |  |
| TREND_DOWN | 115 | 1 | 100.00% | **-0.00217** |  |
| CHOP_HIGHVOL | 9152 | 115 | 24.35% | **-0.00333** |  |
| CHOP_LOWVOL | 84336 | 1286 | 28.30% | **-0.00295** |  |
| PANIC | 1414 | 36 | 41.67% | **-0.00238** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00303

- Last 20% Median Exp: -0.00271

- Drop Ratio: 10.70%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
