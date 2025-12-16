# Turbo V3 Verified Result (008930)

## Meta

- Run ID: `verify_turbo_v3_008930_20251215_092728`
- Timestamp (UTC): `2025-12-15T09:27:28Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `008930` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2809, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1356554.9529700174

## Key Points

- Total Return: -98.64%
- Max Drawdown: -98.67%
- Trades: 2809
- Final Equity: 1,356,555 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1404

- Win Rate: 27.21%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -3.93215

- SQN Score: -15.79611


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 16 | 1 | 0.00% | **-0.00825** |  |
| TREND_DOWN | 18 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2508 | 26 | 42.31% | **0.00398** |  |
| CHOP_LOWVOL | 88248 | 1342 | 26.83% | **-0.00288** |  |
| PANIC | 1308 | 35 | 31.43% | **-0.00463** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00283

- Last 20% Median Exp: -0.00311

- Drop Ratio: -10.01%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
