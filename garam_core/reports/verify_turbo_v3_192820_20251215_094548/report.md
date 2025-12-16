# Turbo V3 Verified Result (192820)

## Meta

- Run ID: `verify_turbo_v3_192820_20251215_094548`
- Timestamp (UTC): `2025-12-15T09:45:48Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `192820` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2796, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1328365.0423767208

## Key Points

- Total Return: -98.67%
- Max Drawdown: -98.73%
- Trades: 2796
- Final Equity: 1,328,365 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1398

- Win Rate: 29.11%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00011

- **Expectancy (Net)**: **-0.00269**

- Net PnL Total: -3.76183

- SQN Score: -11.82243


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 414 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 416 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2669 | 25 | 32.00% | **-0.00294** |  |
| CHOP_LOWVOL | 91003 | 1342 | 28.46% | **-0.00273** |  |
| PANIC | 1312 | 31 | 54.84% | **-0.00089** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00246

- Last 20% Median Exp: -0.00320

- Drop Ratio: -29.92%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
