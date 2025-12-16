# Turbo V3 Verified Result (058470)

## Meta

- Run ID: `verify_turbo_v3_058470_20251215_045303`
- Timestamp (UTC): `2025-12-15T04:53:03Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `058470` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2781, win_rate=0.00%, pnl=None, mdd=0.00%, equity=908807.7275047868

## Key Points

- Total Return: -99.09%
- Max Drawdown: -99.10%
- Trades: 2781
- Final Equity: 908,808 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1390

- Win Rate: 27.48%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00034

- **Expectancy (Net)**: **-0.00314**

- Net PnL Total: -4.36575

- SQN Score: -17.73801


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 86 | 3 | 33.33% | **0.00109** |  |
| TREND_DOWN | 65 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6170 | 68 | 29.41% | **-0.00460** |  |
| CHOP_LOWVOL | 84298 | 1295 | 27.10% | **-0.00303** |  |
| PANIC | 1052 | 24 | 41.67% | **-0.00558** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00318

- Last 20% Median Exp: -0.00298

- Drop Ratio: 6.39%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
