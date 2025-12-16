# Turbo V3 Verified Result (005300)

## Meta

- Run ID: `verify_turbo_v3_005300_20251215_100445`
- Timestamp (UTC): `2025-12-15T10:04:45Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005300` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3106, win_rate=0.00%, pnl=None, mdd=0.00%, equity=778749.2219344834

## Key Points

- Total Return: -99.22%
- Max Drawdown: -99.22%
- Trades: 3106
- Final Equity: 778,749 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1553

- Win Rate: 28.59%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -4.43481

- SQN Score: -22.93664


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 159 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 26 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 503 | 5 | 40.00% | **-0.00647** |  |
| CHOP_LOWVOL | 90335 | 1503 | 28.54% | **-0.00292** |  |
| PANIC | 1605 | 45 | 28.89% | **-0.00021** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00312

- Last 20% Median Exp: -0.00304

- Drop Ratio: 2.79%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
