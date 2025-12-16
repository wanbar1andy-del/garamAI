# Turbo V3 Verified Result (028670)

## Meta

- Run ID: `verify_turbo_v3_028670_20251215_085453`
- Timestamp (UTC): `2025-12-15T08:54:53Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `028670` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3170, win_rate=0.00%, pnl=None, mdd=0.00%, equity=640485.073802927

## Key Points

- Total Return: -99.36%
- Max Drawdown: -99.36%
- Trades: 3170
- Final Equity: 640,485 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1585

- Win Rate: 26.81%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00011

- **Expectancy (Net)**: **-0.00291**

- Net PnL Total: -4.60753

- SQN Score: -24.77316


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 45 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 7 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 410 | 4 | 25.00% | **-0.00667** |  |
| CHOP_LOWVOL | 94290 | 1560 | 26.73% | **-0.00286** |  |
| PANIC | 1006 | 21 | 33.33% | **-0.00565** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00302

- Last 20% Median Exp: -0.00268

- Drop Ratio: 11.32%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
