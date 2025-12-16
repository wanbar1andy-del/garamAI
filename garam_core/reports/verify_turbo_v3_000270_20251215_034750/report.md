# Turbo V3 Verified Result (000270)

## Meta

- Run ID: `verify_turbo_v3_000270_20251215_034750`
- Timestamp (UTC): `2025-12-15T03:47:50Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000270` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2671, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1833488.3213767195

## Key Points

- Total Return: -98.17%
- Max Drawdown: -98.18%
- Trades: 2671
- Final Equity: 1,833,488 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1335

- Win Rate: 27.42%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00005

- **Expectancy (Net)**: **-0.00275**

- Net PnL Total: -3.67637

- SQN Score: -20.42961


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 191 | 1 | 100.00% | **0.01648** |  |
| TREND_DOWN | 312 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 84 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94232 | 1320 | 27.42% | **-0.00275** |  |
| PANIC | 1074 | 14 | 21.43% | **-0.00477** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00286

- Last 20% Median Exp: -0.00251

- Drop Ratio: 12.09%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
