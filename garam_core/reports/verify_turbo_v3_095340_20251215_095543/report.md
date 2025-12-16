# Turbo V3 Verified Result (095340)

## Meta

- Run ID: `verify_turbo_v3_095340_20251215_095543`
- Timestamp (UTC): `2025-12-15T09:55:43Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `095340` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2779, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1352010.770406632

## Key Points

- Total Return: -98.65%
- Max Drawdown: -98.65%
- Trades: 2779
- Final Equity: 1,352,011 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1389

- Win Rate: 27.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00004

- **Expectancy (Net)**: **-0.00276**

- Net PnL Total: -3.83829

- SQN Score: -10.41728


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 140 | 3 | 33.33% | **-0.00687** |  |
| TREND_DOWN | 276 | 1 | 0.00% | **-0.00445** |  |
| CHOP_HIGHVOL | 9445 | 87 | 26.44% | **-0.00416** |  |
| CHOP_LOWVOL | 84849 | 1268 | 27.52% | **-0.00259** |  |
| PANIC | 1023 | 30 | 30.00% | **-0.00550** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00260

- Last 20% Median Exp: -0.00329

- Drop Ratio: -26.68%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
