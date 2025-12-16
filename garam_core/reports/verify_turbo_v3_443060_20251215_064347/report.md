# Turbo V3 Verified Result (443060)

## Meta

- Run ID: `verify_turbo_v3_443060_20251215_064347`
- Timestamp (UTC): `2025-12-15T06:43:47Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `443060` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2617, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1507287.687861169

## Key Points

- Total Return: -98.49%
- Max Drawdown: -98.50%
- Trades: 2617
- Final Equity: 1,507,288 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1308

- Win Rate: 27.45%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -3.66731

- SQN Score: -12.17995


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 405 | 2 | 50.00% | **0.00162** |  |
| TREND_DOWN | 730 | 1 | 0.00% | **-0.00713** |  |
| CHOP_HIGHVOL | 3548 | 46 | 17.39% | **-0.00449** |  |
| CHOP_LOWVOL | 89555 | 1224 | 27.45% | **-0.00271** |  |
| PANIC | 1602 | 35 | 40.00% | **-0.00390** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00260

- Last 20% Median Exp: -0.00306

- Drop Ratio: -17.58%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
